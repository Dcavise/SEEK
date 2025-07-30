"""
Pydantic schemas for User operations.
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr = Field(..., description="User email address")
    username: str | None = Field(
        None, min_length=3, max_length=100, description="Username"
    )
    full_name: str | None = Field(None, max_length=200, description="Full name")
    is_active: bool = Field(default=True, description="User active status")
    role: str = Field(default="user", description="User role")

    @validator("role")
    def validate_role(cls, v: str) -> str:
        """Validate role is one of allowed values."""
        allowed_roles = ["user", "admin", "superuser"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, description="User password")

    @validator("password")
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    email: EmailStr | None = Field(None, description="User email address")
    username: str | None = Field(None, min_length=3, max_length=100)
    full_name: str | None = Field(None, max_length=200)
    is_active: bool | None = Field(None, description="User active status")
    role: str | None = Field(None, description="User role")

    @validator("role", pre=True, always=True)
    def validate_role(cls, v: str | None) -> str | None:
        """Validate role is one of allowed values."""
        if v is None:
            return v
        allowed_roles = ["user", "admin", "superuser"]
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of: {allowed_roles}")
        return v


class UserResponse(UserBase):
    """Schema for user responses."""

    id: int = Field(..., description="User ID")
    is_superuser: bool = Field(..., description="Superuser status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: datetime | None = Field(None, description="Last login timestamp")

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for authentication tokens."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Schema for token data."""

    username: str | None = Field(None, description="Username from token")
