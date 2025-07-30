"""
Security utilities for JWT authentication and authorization.

This module provides comprehensive security features including:
- JWT token generation and validation
- Role-based access control
- Rate limiting
- Security headers
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Bearer token extractor
security = HTTPBearer()


class TokenData(BaseModel):
    """Token data model for JWT payload."""
    
    username: Optional[str] = None
    user_id: Optional[int] = None
    scopes: List[str] = Field(default_factory=list)


class JWTTokens(BaseModel):
    """JWT token response model."""
    
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    scope: str


class UserInDB(BaseModel):
    """User model for database storage."""
    
    id: int
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    scopes: List[str] = Field(default_factory=list)


class SecurityException(HTTPException):
    """Custom security exception."""
    
    def __init__(self, detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
        super().__init__(status_code=status_code, detail=detail)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create access token: {e}")
        raise SecurityException("Failed to create access token")


def verify_token(token: str) -> TokenData:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Decoded token data
        
    Raises:
        SecurityException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        username: Optional[str] = payload.get("sub")
        user_id: Optional[int] = payload.get("user_id")
        scopes: List[str] = payload.get("scopes", [])
        
        if username is None:
            raise SecurityException("Invalid token: missing subject")
            
        return TokenData(username=username, user_id=user_id, scopes=scopes)
        
    except jwt.ExpiredSignatureError:
        raise SecurityException("Token has expired")
    except jwt.JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise SecurityException("Invalid token")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Current user token data
        
    Raises:
        SecurityException: If authentication fails
    """
    return verify_token(credentials.credentials)


class RequireScopes:
    """
    Dependency class for role-based access control.
    
    Usage:
        @app.get("/admin")
        async def admin_endpoint(user: TokenData = Depends(RequireScopes(["admin"]))):
            pass
    """
    
    def __init__(self, required_scopes: List[str]):
        self.required_scopes = required_scopes
    
    def __call__(self, current_user: TokenData = Depends(get_current_user)) -> TokenData:
        """
        Check if user has required scopes.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            User data if authorized
            
        Raises:
            SecurityException: If user lacks required permissions
        """
        if not all(scope in current_user.scopes for scope in self.required_scopes):
            missing_scopes = [s for s in self.required_scopes if s not in current_user.scopes]
            raise SecurityException(
                f"Insufficient permissions. Missing scopes: {missing_scopes}",
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        return current_user


# Predefined scope dependencies for common use cases
require_admin = RequireScopes(["admin"])
require_database_admin = RequireScopes(["database:admin"])
require_monitoring = RequireScopes(["monitoring:read"])
require_monitoring_admin = RequireScopes(["monitoring:admin"])


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Authenticate user with username and password.
    
    This is a placeholder implementation. In production, this would
    query the database for user credentials.
    
    Args:
        username: Username
        password: Plain text password
        
    Returns:
        User data if authentication succeeds, None otherwise
    """
    # TODO: Implement actual user authentication with database
    # This is a placeholder for demonstration
    fake_users_db = {
        "admin": {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "hashed_password": get_password_hash("admin123"),
            "scopes": ["admin", "database:admin", "monitoring:admin"]
        },
        "monitor": {
            "id": 2,
            "username": "monitor",
            "email": "monitor@example.com", 
            "hashed_password": get_password_hash("monitor123"),
            "scopes": ["monitoring:read", "monitoring:admin"]
        }
    }
    
    user_data = fake_users_db.get(username)
    if not user_data:
        return None
        
    if not verify_password(password, user_data["hashed_password"]):
        return None
        
    return UserInDB(**user_data)


def create_tokens_for_user(user: UserInDB) -> JWTTokens:
    """
    Create JWT tokens for authenticated user.
    
    Args:
        user: User data
        
    Returns:
        JWT access token and metadata
    """
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    
    token_data = {
        "sub": user.username,
        "user_id": user.id,
        "scopes": user.scopes
    }
    
    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    
    return JWTTokens(
        access_token=access_token,
        expires_in=settings.access_token_expire_minutes * 60,
        scope=" ".join(user.scopes)
    )


# Rate limiting store (in production, use Redis)
_rate_limit_store: Dict[str, List[datetime]] = {}


def check_rate_limit(request: Request, identifier: str) -> bool:
    """
    Check if request is within rate limits.
    
    Args:
        request: FastAPI request object
        identifier: Client identifier (IP, user ID, etc.)
        
    Returns:
        True if within limits, False otherwise
    """
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=1)
    
    # Clean old requests
    if identifier in _rate_limit_store:
        _rate_limit_store[identifier] = [
            req_time for req_time in _rate_limit_store[identifier]
            if req_time > window_start
        ]
    else:
        _rate_limit_store[identifier] = []
    
    # Check current request count
    current_requests = len(_rate_limit_store[identifier])
    
    if current_requests >= settings.rate_limit_requests_per_minute:
        return False
    
    # Add current request
    _rate_limit_store[identifier].append(now)
    return True


def get_client_identifier(request: Request) -> str:
    """
    Get client identifier for rate limiting.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client identifier string
    """
    # Try to get user from token first
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            token_data = verify_token(token)
            return f"user:{token_data.user_id or token_data.username}"
        except SecurityException:
            pass
    
    # Fall back to IP address
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For")
    
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
        
    return f"ip:{client_ip}"


async def rate_limit_dependency(request: Request) -> None:
    """
    FastAPI dependency for rate limiting.
    
    Args:
        request: FastAPI request object
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    identifier = get_client_identifier(request)
    
    if not check_rate_limit(request, identifier):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )


def add_security_headers(response: Any) -> Any:
    """
    Add security headers to HTTP response.
    
    Args:
        response: FastAPI response object
        
    Returns:
        Response with security headers added
    """
    if settings.enable_security_headers:
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response