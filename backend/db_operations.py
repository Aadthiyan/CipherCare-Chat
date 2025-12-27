"""
Database Operations for User Management
Handles CRUD operations for users, tokens, audit logs, and sessions
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import uuid
from contextlib import contextmanager

from backend.database import get_db_connection

logger = logging.getLogger(__name__)


# ============= USER OPERATIONS =============

def create_user_db(
    username: str,
    email: str,
    password_hash: str,
    full_name: str,
    roles: List[str],
    assigned_patients: List[str],
    department: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Create a new user in database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (
                        username, email, password_hash, full_name, roles, 
                        assigned_patients, department
                    )
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
                    RETURNING id, username, email, full_name, roles, department, 
                             is_active, email_verified, created_at
                """, (
                    username, email, password_hash, full_name,
                    str(roles).replace("'", '"'),
                    str(assigned_patients).replace("'", '"'),
                    department
                ))
                
                result = cur.fetchone()
                if result:
                    return {
                        'id': str(result[0]),
                        'username': result[1],
                        'email': result[2],
                        'full_name': result[3],
                        'roles': result[4],
                        'department': result[5],
                        'is_active': result[6],
                        'email_verified': result[7],
                        'created_at': result[8]
                    }
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, email, password_hash, full_name, roles, 
                           assigned_patients, department, is_active, email_verified,
                           mfa_enabled, mfa_secret, last_login, failed_login_attempts,
                           locked_until, created_at
                    FROM users WHERE username = %s
                """, (username,))
                
                result = cur.fetchone()
                if result:
                    return {
                        'id': str(result[0]),
                        'username': result[1],
                        'email': result[2],
                        'password_hash': result[3],
                        'full_name': result[4],
                        'roles': result[5],
                        'assigned_patients': result[6],
                        'department': result[7],
                        'is_active': result[8],
                        'email_verified': result[9],
                        'mfa_enabled': result[10],
                        'mfa_secret': result[11],
                        'last_login': result[12],
                        'failed_login_attempts': result[13],
                        'locked_until': result[14],
                        'created_at': result[15]
                    }
    except Exception as e:
        logger.error(f"Failed to get user: {e}")
        return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, email, password_hash, full_name, roles, 
                           assigned_patients, department, is_active, email_verified
                    FROM users WHERE email = %s
                """, (email,))
                
                result = cur.fetchone()
                if result:
                    return {
                        'id': str(result[0]),
                        'username': result[1],
                        'email': result[2],
                        'password_hash': result[3],
                        'full_name': result[4],
                        'roles': result[5],
                        'assigned_patients': result[6],
                        'department': result[7],
                        'is_active': result[8],
                        'email_verified': result[9]
                    }
    except Exception as e:
        logger.error(f"Failed to get user by email: {e}")
        return None


def store_verification_token(user_id: str, token: str, expires_in_hours: int = 24) -> bool:
    """Store email verification token for user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
                cur.execute("""
                    UPDATE users 
                    SET email_verification_token = %s,
                        email_verification_expires = %s
                    WHERE id = %s
                """, (token, expires_at, user_id))
                return True
    except Exception as e:
        logger.error(f"Failed to store verification token: {e}")
        return False


def verify_email_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify email verification token and return user if valid"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, email, email_verification_expires
                    FROM users 
                    WHERE email_verification_token = %s
                    AND email_verification_expires > CURRENT_TIMESTAMP
                """, (token,))
                
                result = cur.fetchone()
                if result:
                    return {
                        'id': str(result[0]),
                        'username': result[1],
                        'email': result[2],
                        'expires_at': result[3]
                    }
    except Exception as e:
        logger.error(f"Failed to verify email token: {e}")
    return None


def mark_email_verified(user_id: str) -> bool:
    """Mark user's email as verified"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET email_verified = true,
                        email_verification_token = NULL,
                        email_verification_expires = NULL
                    WHERE id = %s
                """, (user_id,))
                return True
    except Exception as e:
        logger.error(f"Failed to mark email as verified: {e}")
        return False


# ============= OTP OPERATIONS =============

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code (numbers only)"""
    import random
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def store_otp(user_id: str, otp_code: str, expires_in_minutes: int = 15) -> bool:
    """Store OTP code for user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
                cur.execute("""
                    UPDATE users 
                    SET otp_code = %s,
                        otp_expires = %s,
                        otp_attempts = 0
                    WHERE id = %s
                """, (otp_code, expires_at, user_id))
                return True
    except Exception as e:
        logger.error(f"Failed to store OTP: {e}")
        return False


def verify_otp(user_id: str, otp_code: str) -> bool:
    """Verify OTP code for user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get user's OTP
                cur.execute("""
                    SELECT otp_code, otp_expires, otp_attempts
                    FROM users 
                    WHERE id = %s
                """, (user_id,))
                
                result = cur.fetchone()
                if not result:
                    logger.warning(f"User {user_id} not found for OTP verification")
                    return False
                
                stored_otp, expires_at, attempts = result
                
                # Check if OTP expired
                if expires_at < datetime.now():
                    logger.warning(f"OTP expired for user {user_id}")
                    return False
                
                # Check attempts (max 3)
                if attempts >= 3:
                    logger.warning(f"Too many OTP attempts for user {user_id}")
                    return False
                
                # Check if OTP matches
                if stored_otp != otp_code:
                    # Increment attempts
                    cur.execute("""
                        UPDATE users 
                        SET otp_attempts = otp_attempts + 1
                        WHERE id = %s
                    """, (user_id,))
                    logger.warning(f"Invalid OTP for user {user_id}")
                    return False
                
                # OTP is valid, mark email as verified and clear OTP
                cur.execute("""
                    UPDATE users 
                    SET email_verified = true,
                        otp_code = NULL,
                        otp_expires = NULL,
                        otp_attempts = 0
                    WHERE id = %s
                """, (user_id,))
                
                logger.info(f"OTP verified successfully for user {user_id}")
                return True
    except Exception as e:
        logger.error(f"Failed to verify OTP: {e}")
        return False


def update_last_login(username: str) -> bool:
    """Update user's last login timestamp"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET last_login = CURRENT_TIMESTAMP,
                        failed_login_attempts = 0
                    WHERE username = %s
                """, (username,))
                return True
    except Exception as e:
        logger.error(f"Failed to update last login: {e}")
        return False


def increment_failed_login(username: str) -> int:
    """Increment failed login attempts and return new count"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET failed_login_attempts = failed_login_attempts + 1
                    WHERE username = %s
                    RETURNING failed_login_attempts
                """, (username,))
                result = cur.fetchone()
                return result[0] if result else 0
    except Exception as e:
        logger.error(f"Failed to increment failed login: {e}")
        return 0


def lock_user_account(username: str, minutes: int = 15) -> bool:
    """Lock user account for specified minutes"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET locked_until = CURRENT_TIMESTAMP + INTERVAL '%s minutes'
                    WHERE username = %s
                """, (minutes, username))
                return True
    except Exception as e:
        logger.error(f"Failed to lock account: {e}")
        return False


def set_email_verification_token(user_id: str, token: str, expires_hours: int = 24) -> bool:
    """Set email verification token"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET email_verification_token = %s,
                        email_verification_expires = CURRENT_TIMESTAMP + INTERVAL '%s hours'
                    WHERE id = %s
                """, (token, expires_hours, user_id))
                return True
    except Exception as e:
        logger.error(f"Failed to set verification token: {e}")
        return False


def verify_email(token: str) -> bool:
    """Verify email with token"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE users 
                    SET email_verified = true,
                        email_verification_token = NULL,
                        email_verification_expires = NULL
                    WHERE email_verification_token = %s
                      AND email_verification_expires > CURRENT_TIMESTAMP
                    RETURNING id
                """, (token,))
                return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Failed to verify email: {e}")
        return False


# ============= REFRESH TOKEN OPERATIONS =============

def store_refresh_token(user_id: str, token_id: str, expires_days: int = 7) -> bool:
    """Store refresh token in database"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO refresh_tokens (user_id, token_id, expires_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP + INTERVAL '%s days')
                """, (user_id, token_id, expires_days))
                return True
    except Exception as e:
        logger.error(f"Failed to store refresh token: {e}")
        return False


def is_refresh_token_valid(token_id: str) -> bool:
    """Check if refresh token is valid (not revoked and not expired)"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id FROM refresh_tokens
                    WHERE token_id = %s
                      AND is_revoked = false
                      AND expires_at > CURRENT_TIMESTAMP
                """, (token_id,))
                return cur.fetchone() is not None
    except Exception as e:
        logger.error(f"Failed to check refresh token: {e}")
        return False


def revoke_refresh_token(token_id: str, reason: str = "User logout") -> bool:
    """Revoke a refresh token"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE refresh_tokens
                    SET is_revoked = true,
                        revoked_at = CURRENT_TIMESTAMP,
                        revoked_reason = %s
                    WHERE token_id = %s
                """, (reason, token_id))
                return True
    except Exception as e:
        logger.error(f"Failed to revoke refresh token: {e}")
        return False


def revoke_all_user_tokens(user_id: str) -> bool:
    """Revoke all refresh tokens for a user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE refresh_tokens
                    SET is_revoked = true,
                        revoked_at = CURRENT_TIMESTAMP,
                        revoked_reason = 'All tokens revoked'
                    WHERE user_id = %s AND is_revoked = false
                """, (user_id,))
                return True
    except Exception as e:
        logger.error(f"Failed to revoke all tokens: {e}")
        return False


# ============= AUDIT LOG OPERATIONS =============

def log_audit_event(
    user_id: Optional[str],
    username: Optional[str],
    event_type: str,
    event_details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> bool:
    """Log an audit event"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                import json
                cur.execute("""
                    INSERT INTO audit_logs (
                        user_id, username, event_type, event_details,
                        ip_address, user_agent, success, error_message
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                """, (
                    user_id, username, event_type,
                    json.dumps(event_details) if event_details else None,
                    ip_address, user_agent, success, error_message
                ))
                return True
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")
        return False


def get_user_audit_logs(username: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get audit logs for a user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT event_type, event_details, ip_address, success, timestamp
                    FROM audit_logs
                    WHERE username = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (username, limit))
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'event_type': row[0],
                        'event_details': row[1],
                        'ip_address': row[2],
                        'success': row[3],
                        'timestamp': row[4].isoformat() if row[4] else None
                    })
                return results
    except Exception as e:
        logger.error(f"Failed to get audit logs: {e}")
        return []


# ============= SESSION OPERATIONS =============

def create_session(user_id: str, session_token: str, expires_minutes: int, ip_address: str, user_agent: str) -> bool:
    """Create a new session"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sessions (user_id, session_token, expires_at, ip_address, user_agent)
                    VALUES (%s, %s, CURRENT_TIMESTAMP + INTERVAL '%s minutes', %s, %s)
                """, (user_id, session_token, expires_minutes, ip_address, user_agent))
                return True
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        return False


def update_session_activity(session_token: str) -> bool:
    """Update last activity timestamp for session"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE sessions
                    SET last_activity = CURRENT_TIMESTAMP
                    WHERE session_token = %s AND is_active = true
                """, (session_token,))
                return True
    except Exception as e:
        logger.error(f"Failed to update session activity: {e}")
        return False


def invalidate_session(session_token: str) -> bool:
    """Invalidate a session"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE sessions
                    SET is_active = false
                    WHERE session_token = %s
                """, (session_token,))
                return True
    except Exception as e:
        logger.error(f"Failed to invalidate session: {e}")
        return False


# ============= OTP OPERATIONS (EMAIL-FREE VERIFICATION) =============

def generate_otp(length: int = 6) -> str:
    """Generate a random OTP code"""
    import random
    return ''.join(random.choices('0123456789', k=length))


def verify_otp_legacy(user_id: str, otp_code: str) -> bool:
    """Verify OTP code for user"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Get user's OTP details
                cur.execute("""
                    SELECT otp_code, otp_expires, otp_attempts
                    FROM users
                    WHERE id = %s
                """, (user_id,))
                
                result = cur.fetchone()
                if not result:
                    return False
                
                stored_otp, expires_at, attempts = result
                
                # Check if OTP is expired
                if expires_at and datetime.fromisoformat(str(expires_at)) < datetime.now():
                    logger.warning(f"OTP expired for user {user_id}")
                    return False
                
                # Check if too many attempts
                if attempts and attempts >= 5:
                    logger.warning(f"Too many OTP attempts for user {user_id}")
                    return False
                
                # Check if OTP matches
                if stored_otp != otp_code:
                    # Increment attempts
                    cur.execute("""
                        UPDATE users 
                        SET otp_attempts = otp_attempts + 1
                        WHERE id = %s
                    """, (user_id,))
                    logger.warning(f"Invalid OTP attempt for user {user_id}")
                    return False
                
                # OTP is valid - mark email as verified and clear OTP
                cur.execute("""
                    UPDATE users 
                    SET email_verified = true, otp_code = NULL, otp_expires = NULL, otp_attempts = 0
                    WHERE id = %s
                """, (user_id,))
                
                logger.info(f"OTP verified and email marked as verified for user {user_id}")
                return True
                
    except Exception as e:
        logger.error(f"Failed to verify OTP: {e}")
        return False


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, username, email, password_hash, full_name, roles, 
                           assigned_patients, department, is_active, email_verified,
                           created_at
                    FROM users
                    WHERE id = %s
                """, (user_id,))
                
                result = cur.fetchone()
                if result:
                    return {
                        'id': str(result[0]),
                        'username': result[1],
                        'email': result[2],
                        'password_hash': result[3],
                        'full_name': result[4],
                        'roles': result[5],
                        'assigned_patients': result[6],
                        'department': result[7],
                        'is_active': result[8],
                        'email_verified': result[9],
                        'created_at': result[10]
                    }
    except Exception as e:
        logger.error(f"Failed to get user by ID: {e}")
        return None

