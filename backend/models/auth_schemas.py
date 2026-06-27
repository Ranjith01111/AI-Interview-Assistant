"""
Authentication Pydantic Schemas

Request/response models for the auth API endpoints:
  POST /register, POST /login, POST /refresh, GET /me
"""

import re
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Request Schemas ──────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    """Request body for POST /api/v1/auth/register"""
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name of the user",
        examples=["Ranjith Kumar"],
    )
    email: str = Field(
        ...,
        min_length=5,
        max_length=320,
        description="Unique email address",
        examples=["ranjith@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, 1 uppercase, 1 digit, 1 special)",
        examples=["Str0ng!Pass"],
    )
    role: str = Field(
        default="candidate",
        description="User role: admin, recruiter, interviewer, or candidate",
        examples=["candidate"],
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email format validation."""
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce enterprise password policy."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Ensure role is one of the allowed values."""
        allowed = {"admin", "recruiter", "interviewer", "candidate"}
        if v.lower() not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(sorted(allowed))}")
        return v.lower()


class LoginRequest(BaseModel):
    """Request body for POST /api/v1/auth/login"""
    email: str = Field(
        ...,
        description="Registered email address",
        examples=["ranjith@example.com"],
    )
    password: str = Field(
        ...,
        description="Account password",
        examples=["Str0ng!Pass"],
    )

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class RefreshRequest(BaseModel):
    """Request body for POST /api/v1/auth/refresh"""
    refresh_token: str = Field(
        ...,
        description="Valid refresh token from a previous login or refresh",
    )


# ── Response Schemas ─────────────────────────────────────────────────


class TokenResponse(BaseModel):
    """Response for login and refresh endpoints."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        description="Access token lifetime in seconds",
    )
    user: "UserResponse"


class UserResponse(BaseModel):
    """Public user profile (no sensitive fields)."""
    id: uuid.UUID
    name: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Admin response for listing all users."""
    users: List[UserResponse]
    total_count: int


class MessageResponse(BaseModel):
    """Generic success/error message."""
    success: bool
    message: str
    detail: Optional[str] = None
