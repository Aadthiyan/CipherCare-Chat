"""
PostgreSQL Database Setup for CipherCare Authentication
Handles user management, audit logs, and token revocation
"""

# Always load .env before anything else
import os
import sys
from dotenv import load_dotenv

# Load .env - try multiple locations
load_dotenv()  # Current directory
load_dotenv('.env')  # Explicit .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))  # Parent directory

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database connection string from environment (no fallback to local)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL not found in environment")
    logger.error(f"Available env vars: {[k for k in os.environ.keys() if 'DATABASE' in k.upper()]}")
    raise RuntimeError("DATABASE_URL is not set. Please check your .env file.")

# Connection pool
pool: Optional[SimpleConnectionPool] = None


def init_db_pool(min_conn=5, max_conn=20):
    """Initialize connection pool"""
    global pool
    try:
        # Mask password in URL for logging
        masked_url = DATABASE_URL.replace(
            DATABASE_URL.split('@')[0].split('://')[1], 
            '***:***'
        ) if '@' in DATABASE_URL else DATABASE_URL
        logger.info(f"Connecting to database: {masked_url}")
        
        pool = SimpleConnectionPool(
            min_conn, 
            max_conn, 
            DATABASE_URL,
            # Add connection parameters
            connect_timeout=30,
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )
        logger.info(f"✓ Database connection pool initialized (min={min_conn}, max={max_conn})")
        
        # Test connection
        test_conn = pool.getconn()
        try:
            with test_conn.cursor() as cur:
                cur.execute("SELECT 1")
            logger.info("✓ Database connection test successful")
        finally:
            pool.putconn(test_conn)
        
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def close_db_pool():
    """Close all connections in the pool"""
    global pool
    if pool is not None:
        try:
            pool.closeall()
            logger.info("✓ Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {e}")


@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    global pool
    conn = None
    try:
        # Safety check: ensure pool is initialized
        if pool is None:
            logger.error("Database pool not initialized. Calling init_db_pool()...")
            init_db_pool()
        
        if pool is None:
            raise RuntimeError("Failed to initialize database pool. Check DATABASE_URL in .env")
        
        try:
            conn = pool.getconn()
            logger.debug(f"Got connection from pool")
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise
        
        yield conn
        conn.commit()
        logger.debug("Connection committed successfully")
        
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(f"Rollback error: {rollback_error}")
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn and pool is not None:
            try:
                pool.putconn(conn)
                logger.debug("Connection returned to pool")
            except Exception as e:
                logger.error(f"Failed to return connection to pool: {e}")


@contextmanager
def query_db_context(query: str, params: tuple = ()):
    """Simple context manager for executing queries"""
    conn = None
    try:
        global pool
        if pool is None:
            init_db_pool()
        
        conn = pool.getconn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            yield cur
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn and pool:
            pool.putconn(conn)


def query_db(query: str, params: tuple = (), fetch_one: bool = False):
    """Execute a SELECT query and return results"""
    try:
        global pool
        if pool is None:
            init_db_pool()
        
        conn = pool.getconn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch_one:
                    result = cur.fetchone()
                    return dict(result) if result else None
                else:
                    results = cur.fetchall()
                    return [dict(row) for row in results]
        finally:
            pool.putconn(conn)
    except Exception as e:
        logger.error(f"Database query error: {e}")
        raise


def create_tables():
    """Create all required tables"""
    
    # Users table
    users_table = """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        roles JSONB DEFAULT '["resident"]'::jsonb,
        assigned_patients JSONB DEFAULT '[]'::jsonb,
        department VARCHAR(100),
        is_active BOOLEAN DEFAULT true,
        email_verified BOOLEAN DEFAULT false,
        email_verification_token VARCHAR(255),
        email_verification_expires TIMESTAMP,
        otp_code VARCHAR(6),
        otp_expires TIMESTAMP,
        otp_attempts INTEGER DEFAULT 0,
        password_reset_token VARCHAR(255),
        password_reset_expires TIMESTAMP,
        mfa_enabled BOOLEAN DEFAULT false,
        mfa_secret VARCHAR(255),
        last_login TIMESTAMP,
        failed_login_attempts INTEGER DEFAULT 0,
        locked_until TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified);
    """
    
    # Refresh tokens table
    refresh_tokens_table = """
    CREATE TABLE IF NOT EXISTS refresh_tokens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token_id VARCHAR(255) UNIQUE NOT NULL,
        is_revoked BOOLEAN DEFAULT false,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        revoked_at TIMESTAMP,
        revoked_reason VARCHAR(255)
    );
    
    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_id ON refresh_tokens(token_id);
    CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
    """
    
    # Audit logs table
    audit_logs_table = """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        username VARCHAR(50),
        event_type VARCHAR(50) NOT NULL,
        event_details JSONB,
        ip_address VARCHAR(45),
        user_agent TEXT,
        success BOOLEAN DEFAULT true,
        error_message TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON audit_logs(event_type);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_username ON audit_logs(username);
    """
    
    # Session management table
    sessions_table = """
    CREATE TABLE IF NOT EXISTS sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        session_token VARCHAR(255) UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address VARCHAR(45),
        user_agent TEXT,
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
    CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
    """
    
    # Password history table (for password policy)
    password_history_table = """
    CREATE TABLE IF NOT EXISTS password_history (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_password_history_user_id ON password_history(user_id);
    """
    
    # Updated_at trigger function
    trigger_function = """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """
    
    # Trigger for users table
    trigger = """
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(users_table)
                cur.execute(refresh_tokens_table)
                cur.execute(audit_logs_table)
                cur.execute(sessions_table)
                cur.execute(password_history_table)
                cur.execute(trigger_function)
                cur.execute(trigger)
                logger.info("✓ All database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False


def migrate_fake_users():
    """Migrate FAKE_USERS_DB to PostgreSQL"""
    import bcrypt
    
    fake_users = {
        "attending": {
            "username": "attending",
            "email": "attending@cipercare.com",
            "full_name": "Dr. Smith (Attending)",
            "roles": ["attending", "admin"],
            "assigned_patients": ["any"],
            "department": "Internal Medicine"
        },
        "resident": {
            "username": "resident",
            "email": "resident@cipercare.com",
            "full_name": "Dr. Doe (Resident)",
            "roles": ["resident"],
            "assigned_patients": ["P123", "P456"],
            "department": "Surgery"
        }
    }
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                for username, user_data in fake_users.items():
                    # Check if user exists
                    cur.execute("SELECT id FROM users WHERE username = %s", (username,))
                    if cur.fetchone():
                        logger.info(f"User {username} already exists, skipping")
                        continue
                    
                    # Hash default password
                    password_hash = bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode()
                    
                    # Insert user
                    cur.execute("""
                        INSERT INTO users (username, email, full_name, password_hash, roles, assigned_patients, department, email_verified, is_active)
                        VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, true, true)
                    """, (
                        user_data["username"],
                        user_data["email"],
                        user_data["full_name"],
                        password_hash,
                        str(user_data["roles"]).replace("'", '"'),
                        str(user_data["assigned_patients"]).replace("'", '"'),
                        user_data["department"]
                    ))
                    
                    logger.info(f"✓ Migrated user: {username}")
        
        logger.info("✓ User migration completed")
        return True
    except Exception as e:
        logger.error(f"Failed to migrate users: {e}")
        return False


def setup_database():
    """Complete database setup"""
    logger.info("Starting database setup...")
    
    if not init_db_pool():
        return False
    
    if not create_tables():
        return False
    
    if not migrate_fake_users():
        return False
    
    logger.info("✓ Database setup completed successfully")
    return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_database()
