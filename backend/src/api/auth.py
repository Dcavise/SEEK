"""
Authentication API endpoints.

Provides secure authentication and authorization endpoints for the
microschool property intelligence platform.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from ..core.security import (
    JWTTokens,
    TokenData,
    authenticate_user,
    create_tokens_for_user,
    get_current_user,
    rate_limit_dependency,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request model."""
    
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class UserProfile(BaseModel):
    """User profile response model."""
    
    id: int
    username: str
    email: str
    scopes: list[str]
    is_active: bool


@router.post("/login", response_model=JWTTokens)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    _: None = Depends(rate_limit_dependency)
) -> JWTTokens:
    """
    Authenticate user and return JWT access token.
    
    Args:
        request: FastAPI request object
        form_data: OAuth2 form data with username and password
        
    Returns:
        JWT access token and metadata
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Authenticate user
        user = authenticate_user(form_data.username, form_data.password)
        
        if not user:
            logger.warning(f"Failed login attempt for username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        tokens = create_tokens_for_user(user)
        
        logger.info(f"Successful login for user: {user.username}")
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.post("/token", response_model=JWTTokens)
async def login_for_access_token(
    request: Request,
    login_data: LoginRequest,
    _: None = Depends(rate_limit_dependency)
) -> JWTTokens:
    """
    Alternative login endpoint accepting JSON payload.
    
    Args:
        request: FastAPI request object
        login_data: Login credentials
        
    Returns:
        JWT access token and metadata
    """
    try:
        user = authenticate_user(login_data.username, login_data.password)
        
        if not user:
            logger.warning(f"Failed login attempt for username: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        tokens = create_tokens_for_user(user)
        
        logger.info(f"Successful login for user: {user.username}")
        
        return tokens
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    current_user: TokenData = Depends(get_current_user)
) -> UserProfile:
    """
    Get current user profile information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User profile data
    """
    try:
        # In production, this would fetch user data from database
        # For now, return data from token
        return UserProfile(
            id=current_user.user_id or 0,
            username=current_user.username or "unknown",
            email=f"{current_user.username}@example.com",
            scopes=current_user.scopes,
            is_active=True
        )
        
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.post("/verify-token")
async def verify_token(
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Verify JWT token validity.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Token validation result
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "username": current_user.username,
        "scopes": current_user.scopes,
        "message": "Token is valid"
    }


@router.post("/logout")
async def logout(
    current_user: TokenData = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Logout user (invalidate token).
    
    Note: With JWT tokens, logout is handled client-side by discarding the token.
    In production, you might implement a token blacklist for immediate invalidation.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Logout confirmation
    """
    logger.info(f"User logout: {current_user.username}")
    
    return {
        "message": "Successfully logged out",
        "username": current_user.username or "unknown"
    }