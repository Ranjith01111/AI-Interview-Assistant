"""
Authentication Router

Defines the FastAPI endpoints for:
  • POST /auth/register
  • POST /auth/login
  • POST /auth/refresh
  • GET  /auth/me
  • GET  /auth/users (Admin-only)
  • POST /auth/users/{id}/deactivate (Admin-only)
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from backend.core.config import settings
from backend.core.rate_limiter import limiter
from backend.core.security import get_current_active_user, require_role
from backend.db.session import get_db
from backend.models.user import User, UserRole
from backend.models.auth_schemas import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    UserListResponse,
    MessageResponse,
)
from backend.services.auth_service import (
    register_user,
    authenticate_user,
    refresh_access_token,
)
from backend.services.audit_service import log_audit_event

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Registers a new user on the platform.
    Passwords will be checked for strength and stored as a secure bcrypt hash.
    By default, registers as a 'candidate' role unless specified otherwise.
    """
    return await register_user(request=request, data=data, db=db)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue tokens"
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Log in with an email and password to retrieve a JWT Token pair:
      - **access_token**: 30-minute expiration, used in standard Authorization Headers.
      - **refresh_token**: 7-day expiration, stored/managed via rotating Redis states.
    """
    user, access_token, refresh_token = await authenticate_user(
        request=request,
        credentials=credentials,
        db=db
    )
    
    expires_in_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in_seconds,
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange refresh token for a new JWT pair"
)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh(
    request: Request,
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a valid refresh token to obtain a fresh access token and a brand new
    rotating refresh token. Previous refresh tokens are immediately revoked.
    """
    user, access_token, refresh_token = await refresh_access_token(
        request=request,
        refresh_token=payload.refresh_token,
        db=db
    )
    
    expires_in_seconds = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in_seconds,
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve current user's profile"
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns the profile details of the currently authenticated active user.
    """
    return UserResponse.model_validate(current_user)


# ── Role-Based Route Guards (Admin Only) ──────────────────────────────

@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all registered users (Admin only)"
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
):
    """
    Admin-only endpoint to retrieve all registered accounts on the platform.
    """
    # Query all users
    query = select(User).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = result.scalars().all()

    # Get total count
    count_query = select(func.count()).select_from(User)
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total_count=total_count
    )


@router.post(
    "/users/{user_id}/deactivate",
    response_model=MessageResponse,
    summary="Deactivate a user account (Admin only)"
)
async def deactivate_user(
    request: Request,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.RECRUITER)),
):
    """
    Admin-only endpoint to soft-delete/deactivate a user.
    Prevents the user from subsequent logins or API requests.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own administrative account.",
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    target_user = result.scalars().first()

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested user account was not found.",
        )

    # SECURITY: Prevent privilege escalation — recruiters cannot deactivate admins
    if current_user.role == UserRole.RECRUITER.value and target_user.role == UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiters cannot deactivate admin accounts. Only admins can manage other admins.",
        )

    if not target_user.is_active:
        return MessageResponse(
            success=True,
            message="The user account is already deactivated."
        )

    # Deactivate and persist to database
    target_user.is_active = False
    db.add(target_user)
    await db.commit()
    await db.refresh(target_user)

    # Log the administration deactivation event
    await log_audit_event(
        db=db,
        action="account_deactivated",
        status="success",
        user_id=user_id,
        details={"admin_user_id": str(current_user.id)},
        request=request,
    )

    return MessageResponse(
        success=True,
        message=f"User {target_user.email} has been deactivated successfully."
    )
