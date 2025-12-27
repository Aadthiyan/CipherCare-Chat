"""
Clean Database - Remove All Mock Users
Clears all users, tokens, sessions, and audit logs for fresh start
"""
import sys
import os

# Load .env from the root directory (where this script is)
from dotenv import load_dotenv
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_path)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def clean_database():
    """Remove all users and related data"""
    try:
        from backend.database import get_db_connection
        
        logger.info("=" * 60)
        logger.info("🧹 Cleaning Database - Removing All Users")
        logger.info("=" * 60)
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get current counts
                cur.execute("SELECT COUNT(*) FROM users")
                user_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM audit_logs")
                audit_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM refresh_tokens")
                token_count = cur.fetchone()[0]
                
                cur.execute("SELECT COUNT(*) FROM sessions")
                session_count = cur.fetchone()[0]
                
                logger.info(f"\n📊 Current Database State:")
                logger.info(f"   Users: {user_count}")
                logger.info(f"   Audit Logs: {audit_count}")
                logger.info(f"   Refresh Tokens: {token_count}")
                logger.info(f"   Sessions: {session_count}")
                
                if user_count == 0:
                    logger.info("\n✅ Database is already empty - nothing to clean")
                    return True
                
                # Confirm deletion
                logger.info(f"\n⚠️  WARNING: This will DELETE ALL {user_count} users and related data!")
                response = input("   Type 'YES' to confirm deletion: ")
                
                if response.strip().upper() != 'YES':
                    logger.info("\n❌ Deletion cancelled")
                    return False
                
                logger.info("\n🗑️  Deleting data...")
                
                # Delete in correct order (respecting foreign keys)
                cur.execute("DELETE FROM password_history")
                logger.info("   ✓ Cleared password history")
                
                cur.execute("DELETE FROM sessions")
                logger.info("   ✓ Cleared sessions")
                
                cur.execute("DELETE FROM refresh_tokens")
                logger.info("   ✓ Cleared refresh tokens")
                
                cur.execute("DELETE FROM audit_logs")
                logger.info("   ✓ Cleared audit logs")
                
                cur.execute("DELETE FROM users")
                logger.info("   ✓ Cleared all users")
                
                # Reset sequences (optional)
                logger.info("\n🔄 Resetting sequences...")
                cur.execute("""
                    SELECT setval(pg_get_serial_sequence('users', 'id'), 1, false);
                    SELECT setval(pg_get_serial_sequence('audit_logs', 'id'), 1, false);
                    SELECT setval(pg_get_serial_sequence('refresh_tokens', 'id'), 1, false);
                    SELECT setval(pg_get_serial_sequence('sessions', 'id'), 1, false);
                """)
                
                logger.info("\n" + "=" * 60)
                logger.info("✅ Database Cleaned Successfully!")
                logger.info("=" * 60)
                logger.info("\n📝 Next Steps:")
                logger.info("   1. Go to http://localhost:3000/auth/signup")
                logger.info("   2. Register your first admin user")
                logger.info("   3. Check email for verification link")
                logger.info("   4. Login and start using the system")
                
                return True
                
    except Exception as e:
        logger.error(f"\n❌ Error cleaning database: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_current_users():
    """Display all current users in the database"""
    try:
        from backend.database import get_db_connection
        
        logger.info("\n📋 Current Users in Database:")
        logger.info("-" * 60)
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT username, email, full_name, roles, is_active, email_verified, created_at
                    FROM users
                    ORDER BY created_at
                """)
                
                users = cur.fetchall()
                
                if not users:
                    logger.info("   (No users found)")
                else:
                    for user in users:
                        logger.info(f"\n   Username: {user[0]}")
                        logger.info(f"   Email: {user[1]}")
                        logger.info(f"   Name: {user[2]}")
                        logger.info(f"   Roles: {user[3]}")
                        logger.info(f"   Active: {user[4]}")
                        logger.info(f"   Verified: {user[5]}")
                        logger.info(f"   Created: {user[6]}")
                        logger.info("   " + "-" * 40)
                
                logger.info(f"\nTotal Users: {len(users)}")
                
    except Exception as e:
        logger.error(f"\n❌ Error fetching users: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clean database and remove all users")
    parser.add_argument("--list", action="store_true", help="List current users without deleting")
    parser.add_argument("--force", action="store_true", help="Delete without confirmation")
    args = parser.parse_args()
    
    # Initialize database connection
    from backend.database import init_db_pool
    if not init_db_pool():
        logger.error("❌ Failed to connect to database")
        sys.exit(1)
    
    if args.list:
        show_current_users()
    else:
        if args.force:
            # Skip confirmation
            logger.info("⚠️  Force mode - deleting without confirmation")
        success = clean_database()
        sys.exit(0 if success else 1)
