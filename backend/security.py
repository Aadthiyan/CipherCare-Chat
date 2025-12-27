"""
Security utilities and middleware for CipherCare
CSRF protection, security headers, rate limiting, and audit logging
"""

import os
import secrets
import logging
from typing import Optional
from datetime import datetime
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.db_operations import log_audit_event

logger = logging.getLogger(__name__)

# CSRF Token Storage (in production, use Redis or database)
CSRF_TOKENS = set()


# ============= SECURITY HEADERS MIDDLEWARE =============

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # HSTS (HTTP Strict Transport Security) - only in production with HTTPS
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


# ============= CSRF PROTECTION =============

def generate_csrf_token() -> str:
    """Generate a new CSRF token"""
    token = secrets.token_urlsafe(32)
    CSRF_TOKENS.add(token)
    return token


def validate_csrf_token(token: str) -> bool:
    """Validate CSRF token"""
    if token in CSRF_TOKENS:
        CSRF_TOKENS.remove(token)  # One-time use
        return True
    return False


async def require_csrf_token(request: Request):
    """Dependency to require CSRF token for state-changing operations"""
    csrf_token = request.headers.get("X-CSRF-Token")
    
    if not csrf_token or not validate_csrf_token(csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing CSRF token"
        )
    
    return csrf_token


# ============= AUDIT LOGGING =============

class AuditMiddleware(BaseHTTPMiddleware):
    """Audit log all authentication and data access events"""
    
    async def dispatch(self, request: Request, call_next):
        # Extract info
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        path = request.url.path
        
        # Get user from request state (if authenticated)
        user_id = getattr(request.state, "user_id", None)
        username = getattr(request.state, "username", None)
        
        # Determine if this is an audit-worthy event
        audit_paths = [
            "/auth/login", "/auth/signup", "/auth/logout",
            "/api/v1/query", "/api/v1/upload", "/auth/password"
        ]
        
        should_audit = any(path.startswith(p) for p in audit_paths)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log successful requests
            if should_audit and 200 <= response.status_code < 300:
                event_type = f"{method}_{path.split('/')[-1]}"
                log_audit_event(
                    user_id=user_id,
                    username=username,
                    event_type=event_type,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=True
                )
            
            return response
            
        except Exception as e:
            # Log failed requests
            if should_audit:
                event_type = f"{method}_{path.split('/')[-1]}_failed"
                log_audit_event(
                    user_id=user_id,
                    username=username,
                    event_type=event_type,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    error_message=str(e)
                )
            raise


# ============= HTTPS ENFORCEMENT =============

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Redirect HTTP to HTTPS in production"""
    
    async def dispatch(self, request: Request, call_next):
        # Only enforce in production
        if os.getenv("ENVIRONMENT") != "production":
            return await call_next(request)
        
        # Check if request is HTTP
        if request.url.scheme == "http":
            # Redirect to HTTPS
            https_url = str(request.url).replace("http://", "https://", 1)
            return JSONResponse(
                status_code=status.HTTP_301_MOVED_PERMANENTLY,
                headers={"Location": https_url}
            )
        
        return await call_next(request)


# ============= INPUT SANITIZATION =============

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters (except newlines and tabs)
    text = ''.join(char for char in text if char in '\n\t' or not char.isspace() or char == ' ')
    
    return text.strip()


def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email)) and len(email) <= 255


def validate_username(username: str) -> bool:
    """Validate username format"""
    import re
    # Alphanumeric, underscore, hyphen only, 3-50 chars
    pattern = r'^[a-zA-Z0-9_-]{3,50}$'
    return bool(re.match(pattern, username))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if len(password) > 128:
        return False, "Password too long"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    
    strength = sum([has_upper, has_lower, has_digit, has_special])
    
    if strength < 3:
        return False, "Password must contain at least 3 of: uppercase, lowercase, numbers, special characters"
    
    return True, "Password strength acceptable"


# ============= RATE LIMITING HELPERS =============

class RateLimitStorage:
    """Simple in-memory rate limit storage (use Redis in production)"""
    
    def __init__(self):
        self.storage = {}
    
    def increment(self, key: str, window_seconds: int = 60) -> int:
        """Increment counter for key and return new count"""
        now = datetime.now().timestamp()
        
        # Clean old entries
        if key in self.storage:
            self.storage[key] = [
                ts for ts in self.storage[key]
                if now - ts < window_seconds
            ]
        else:
            self.storage[key] = []
        
        # Add new entry
        self.storage[key].append(now)
        return len(self.storage[key])
    
    def get_count(self, key: str, window_seconds: int = 60) -> int:
        """Get current count for key"""
        if key not in self.storage:
            return 0
        
        now = datetime.now().timestamp()
        valid_entries = [
            ts for ts in self.storage[key]
            if now - ts < window_seconds
        ]
        
        self.storage[key] = valid_entries
        return len(valid_entries)
    
    def reset(self, key: str):
        """Reset counter for key"""
        if key in self.storage:
            del self.storage[key]


# Global rate limit storage
rate_limit_storage = RateLimitStorage()


def check_rate_limit(identifier: str, max_attempts: int, window_seconds: int = 60) -> bool:
    """Check if rate limit is exceeded"""
    count = rate_limit_storage.get_count(identifier, window_seconds)
    return count < max_attempts


def increment_rate_limit(identifier: str, window_seconds: int = 60) -> int:
    """Increment rate limit counter and return new count"""
    return rate_limit_storage.increment(identifier, window_seconds)


# ============= REQUEST CONTEXT HELPERS =============

def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    # Check X-Forwarded-For header (from proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Get user agent from request"""
    return request.headers.get("User-Agent", "unknown")


# ============= PASSWORD POLICY =============

def is_password_in_history(user_id: str, new_password_hash: str, history_limit: int = 5) -> bool:
    """Check if password was used recently (implement with database)"""
    # TODO: Query password_history table
    # For now, return False (not in history)
    return False


def add_password_to_history(user_id: str, password_hash: str) -> bool:
    """Add password to history"""
    try:
        from backend.database import get_db_connection
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO password_history (user_id, password_hash)
                    VALUES (%s, %s)
                """, (user_id, password_hash))
                return True
    except Exception as e:
        logger.error(f"Failed to add password to history: {e}")
        return False


# ============= SECURITY MONITORING =============

def detect_suspicious_activity(
    username: str,
    ip_address: str,
    event_type: str,
    user_agent: str
) -> tuple[bool, str]:
    """Detect suspicious login activity"""
    # Check for rapid login attempts
    rate_key = f"login:{username}:{ip_address}"
    attempts = rate_limit_storage.get_count(rate_key, window_seconds=300)  # 5 minutes
    
    if attempts > 10:
        return True, "Too many login attempts from this IP"
    
    # TODO: Add more sophisticated detection:
    # - Login from unusual location
    # - Login from multiple IPs simultaneously
    # - Login at unusual time
    # - Unusual user agent
    
    return False, ""


# ============= TOKEN BLACKLIST =============

class TokenBlacklist:
    """Manage revoked/blacklisted tokens"""
    
    def __init__(self):
        self.blacklist = set()
    
    def add(self, token: str):
        """Add token to blacklist"""
        self.blacklist.add(token)
    
    def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        return token in self.blacklist
    
    def remove(self, token: str):
        """Remove token from blacklist"""
        if token in self.blacklist:
            self.blacklist.remove(token)


# Global token blacklist
token_blacklist = TokenBlacklist()
