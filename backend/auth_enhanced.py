"""
Enhanced Authentication Module with Database Support
Supports JWT tokens, password hashing, user registration, and RBAC
"""

import os
import json
import logging
import bcrypt
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import PyJWTError
import secrets

from backend.models import TokenData, UserResponse
from backend.email_service import email_service

logger = logging.getLogger(__name__)

# Settings
ALGORITHM = "HS256"
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hackathon_secret_key_change_me_in_production")
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- User Database (In-Memory for MVP, replace with PostgreSQL) ---
# This simulates a users table in PostgreSQL
USERS_DB: Dict[str, Dict[str, Any]] = {
    "attending": {
        "username": "attending",
        "email": "attending@cipercare.com",
        "full_name": "Dr. Smith (Attending)",
        "password_hash": bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
        "roles": ["attending", "admin"],
        "assigned_patients": ["any"],
        "department": "Internal Medicine",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "email_verified": True
    },
    "resident": {
        "username": "resident",
        "email": "resident@cipercare.com",
        "full_name": "Dr. Doe (Resident)",
        "password_hash": bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
        "roles": ["resident"],
        "assigned_patients": ["P123", "P456"],
        "department": "Surgery",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "email_verified": True
    }
}

# Password reset tokens (in-memory, would be in DB)
PASSWORD_RESET_TOKENS: Dict[str, Dict[str, Any]] = {}

# Refresh tokens (in-memory, would be in DB with revocation list)
REFRESH_TOKENS: Dict[str, Dict[str, Any]] = {}


# --- Password Hashing ---
def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# --- Token Management ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(username: str) -> str:
    """Create JWT refresh token"""
    token_id = secrets.token_urlsafe(32)
    data = {
        "sub": username,
        "jti": token_id,
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    }
    
    # Store token in memory (would be in DB)
    REFRESH_TOKENS[token_id] = {
        "username": username,
        "created_at": datetime.utcnow().isoformat(),
        "is_revoked": False
    }
    
    encoded_jwt = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


# --- User Management ---
def get_user(username: str) -> Optional[Dict[str, Any]]:
    """Get user from database"""
    return USERS_DB.get(username)


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email"""
    for user in USERS_DB.values():
        if user.get("email") == email:
            return user
    return None


def create_user(username: str, email: str, password: str, full_name: str, 
                role: str = "resident", department: Optional[str] = None) -> Dict[str, Any]:
    """Create new user in database"""
    
    # Validation
    if username in USERS_DB:
        raise ValueError(f"Username {username} already exists")
    
    if get_user_by_email(email):
        raise ValueError(f"Email {email} already registered")
    
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    
    # Create user
    user_data = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "password_hash": hash_password(password),
        "roles": [role],  # Single role on creation
        "assigned_patients": ["P123", "P456"] if role == "resident" else ["any"],
        "department": department,
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "email_verified": False,  # Requires email confirmation
        "verification_token": verification_token,
        "last_login": None
    }
    
    USERS_DB[username] = user_data
    logger.info(f"User created: {username}")
    
    # Send verification email
    try:
        email_sent = email_service.send_verification_email(email, full_name, verification_token)
        if email_sent:
            logger.info(f"✓ Verification email sent to {email}")
        else:
            logger.warning(f"⚠️ Verification email not sent to {email} (email service may be disabled)")
            # Print OTP to console for development
            logger.info(f"📧 VERIFICATION TOKEN for {email}: {verification_token}")
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        logger.info(f"📧 VERIFICATION TOKEN for {email}: {verification_token}")
    
    return user_data


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate user with username and password from PostgreSQL database"""
    import bcrypt
    from backend.db_operations import get_user_by_username, update_last_login
    
    # Get user from database
    user = get_user_by_username(username)
    
    if not user:
        logger.warning(f"Authentication failed: user {username} not found")
        return None
    
    if not user.get("is_active"):
        logger.warning(f"Authentication failed: user {username} is inactive")
        return None
    
    # Verify password using bcrypt
    password_hash = user.get("password_hash", "")
    try:
        if not bcrypt.checkpw(password.encode(), password_hash.encode()):
            logger.warning(f"Authentication failed: invalid password for {username}")
            return None
    except Exception as e:
        logger.warning(f"Authentication failed: password verification error for {username}: {e}")
        return None
    
    # Update last login in database
    update_last_login(username)
    
    logger.info(f"User authenticated: {username}")
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    """Get current authenticated user from token"""
    from backend.db_operations import get_user_by_username
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if not payload:
        raise credentials_exception
    
    username: str = payload.get("sub")
    token_type: str = payload.get("type", "access")
    roles: List[str] = payload.get("roles", [])
    
    if username is None or token_type != "access":
        raise credentials_exception
    
    # Get user from database
    user = get_user_by_username(username)
    if not user:
        raise credentials_exception
    
    return TokenData(username=username, roles=user.get("roles", []))


# --- RBAC Helpers ---
def require_role(required_role: str):
    """Decorator to require specific role"""
    async def role_checker(user: TokenData = Depends(get_current_user)):
        if required_role not in user.roles and "admin" not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role"
            )
        return user
    return role_checker


def check_patient_access(user: TokenData, patient_id: str) -> bool:
    """Check if user can access patient"""
    user_record = get_user(user.username)
    if not user_record:
        return False
    
    # Admins and attendings can access any patient
    if "admin" in user.roles or "attending" in user.roles:
        return True
    
    # Residents can only access assigned patients
    assigned_patients = user_record.get("assigned_patients", [])
    if "any" in assigned_patients or patient_id in assigned_patients:
        return True
    
    return False


# --- Password Reset ---
def create_password_reset_token(email: str) -> Optional[str]:
    """Create password reset token"""
    user = get_user_by_email(email)
    if not user:
        logger.warning(f"Password reset requested for non-existent email: {email}")
        return None
    
    token = secrets.token_urlsafe(32)
    PASSWORD_RESET_TOKENS[token] = {
        "email": email,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "used": False
    }
    
    logger.info(f"Password reset token created for {email}")
    return token


def reset_password(token: str, new_password: str) -> bool:
    """Reset password with reset token"""
    reset_data = PASSWORD_RESET_TOKENS.get(token)
    
    if not reset_data:
        logger.warning("Invalid password reset token")
        return False
    
    if reset_data.get("used"):
        logger.warning("Password reset token already used")
        return False
    
    expires_at = datetime.fromisoformat(reset_data.get("expires_at"))
    if datetime.utcnow() > expires_at:
        logger.warning("Password reset token expired")
        return False
    
    email = reset_data.get("email")
    user = get_user_by_email(email)
    
    if not user:
        return False
    
    # Update password
    user["password_hash"] = hash_password(new_password)
    reset_data["used"] = True
    
    logger.info(f"Password reset for {email}")
    return True


def change_password(username: str, old_password: str, new_password: str) -> bool:
    """Change password for authenticated user"""
    user = get_user(username)
    
    if not user:
        return False
    
    # Verify old password
    if not verify_password(old_password, user.get("password_hash", "")):
        logger.warning(f"Password change failed for {username}: invalid old password")
        return False
    
    # Update password
    user["password_hash"] = hash_password(new_password)
    logger.info(f"Password changed for {username}")
    return True


def revoke_refresh_token(jti: str) -> bool:
    """Revoke a refresh token"""
    token_data = REFRESH_TOKENS.get(jti)
    if token_data:
        token_data["is_revoked"] = True
        logger.info(f"Refresh token revoked: {jti}")
        return True
    return False


# Legacy support for old code
FAKE_USERS_DB = USERS_DB
