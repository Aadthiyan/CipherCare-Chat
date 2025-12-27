import os
import json
import logging
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import PyJWTError
from urllib.request import urlopen

from backend.models import TokenData

logger = logging.getLogger(__name__)

# Settings
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-tenant.auth0.com")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://cipercare/api") 
ALGORITHM = "RS256"

# Fallback 
LOCAL_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hackathon_secret_key_change_me")
LOCAL_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Mock DB
FAKE_USERS_DB = {
    "attending": {
        "username": "attending",
        "full_name": "Dr. Smith",
        "email": "smith@cipercare.com",
        "hashed_password": "password123", 
        "roles": ["attending", "admin"],
        "assigned_patients": ["any"] 
    },
    "resident": {
        "username": "resident",
        "full_name": "Dr. Doe",
        "email": "doe@cipercare.com",
        "hashed_password": "password123",
        "roles": ["resident"],
        "assigned_patients": ["P123", "P456"] 
    }
}

class Auth0Validator:
    def verify(self, token: str):
        # Stub for logic - simply fail so fallback takes over
        raise Exception("Auth0 Not Configured")

auth0_validator = Auth0Validator()

def verify_password(plain_password, hashed_password):
    return plain_password == hashed_password 

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # Local Dev Token Generation
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    # PyJWT uses 'exp' automatically
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, LOCAL_SECRET_KEY, algorithm=LOCAL_ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Hybrid Check
    try:
        # 1. Try Auth0 (Will fail in dev)
        payload = auth0_validator.verify(token)
        return TokenData(username=payload.get("sub"), roles=[])
    except:
        # 2. Try Local
        try:
            payload = jwt.decode(token, LOCAL_SECRET_KEY, algorithms=[LOCAL_ALGORITHM])
            username: str = payload.get("sub")
            roles: List[str] = payload.get("roles", [])
            if username is None:
                raise credentials_exception
            return TokenData(username=username, roles=roles)
        except PyJWTError:
            raise credentials_exception

# RBAC Decorator Logic
def require_role(required_role: str):
    def role_checker(user: TokenData = Depends(get_current_user)):
        if required_role not in user.roles and "admin" not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role"
            )
        return user
    return role_checker

def check_patient_access(user: TokenData, patient_id: str):
    """
    Check if user has access to a specific patient.
    First tries database, falls back to FAKE_USERS_DB for testing.
    """
    try:
        from backend.database import query_db
        
        # Query database for user
        result = query_db(
            "SELECT roles, assigned_patients FROM users WHERE username = %s",
            (user.username,),
            fetch_one=True
        )
        
        if result:
            # Parse JSONB fields from database
            roles = result.get("roles", [])
            assigned = result.get("assigned_patients", [])
            
            # Check access
            if "any" in assigned or "admin" in roles:
                return True
            if patient_id in assigned:
                return True
            return False
    except Exception as e:
        logger.warning(f"Database query failed for patient access check: {str(e)}, falling back to FAKE_USERS_DB")
    
    # Fallback to in-memory DB for testing
    user_record = FAKE_USERS_DB.get(user.username)
    if not user_record:
        return False
        
    assigned = user_record.get("assigned_patients", [])
    if "any" in assigned or "admin" in user.roles:
        return True
    if patient_id in assigned:
        return True
    return False
