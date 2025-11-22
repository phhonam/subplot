"""
Simple authentication system for admin interface
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

# Simple in-memory session storage (use Redis or database in production)
admin_sessions = {}

# JWT settings
JWT_SECRET = os.environ.get("ADMIN_JWT_SECRET", secrets.token_urlsafe(32))
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Admin credentials (use environment variables in production)
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH") or hashlib.sha256("admin123".encode()).hexdigest()

security = HTTPBearer()

def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def create_access_token(username: str) -> str:
    """Create a JWT access token"""
    payload = {
        "username": username,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a JWT access token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def authenticate_admin(username: str, password: str) -> bool:
    """Authenticate admin credentials"""
    if username != ADMIN_USERNAME:
        return False
    
    return verify_password(password, ADMIN_PASSWORD_HASH)

def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated admin user"""
    token = credentials.credentials
    payload = verify_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

def require_admin_auth():
    """Dependency to require admin authentication"""
    return Depends(get_current_admin)

# Login endpoint data models
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = JWT_EXPIRATION_HOURS * 3600

class AuthStatus(BaseModel):
    authenticated: bool
    username: Optional[str] = None
    expires_at: Optional[datetime] = None

def check_auth_status(token: Optional[str] = None) -> AuthStatus:
    """Check authentication status"""
    if not token:
        return AuthStatus(authenticated=False)
    
    payload = verify_access_token(token)
    if payload is None:
        return AuthStatus(authenticated=False)
    
    return AuthStatus(
        authenticated=True,
        username=payload.get("username"),
        expires_at=datetime.fromtimestamp(payload.get("exp", 0))
    )
