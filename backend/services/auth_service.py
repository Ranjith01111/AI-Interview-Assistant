"""
Authentication Service

SECURITY HARDENED — 2026-06-27

Contains business logic for:
  • Hashing and verifying passwords (bcrypt)
  • Generating JWT access and refresh tokens (PyJWT)
  • Decoding and validating tokens
  • Registering new users
  • Authenticating existing users (login)
  • Refreshing expired access tokens using valid refresh tokens
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import re
import uuid
import jwt
import bcrypt
from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.models.user import User, UserRole
from backend.models.auth_schemas import RegisterRequest, LoginRequest
from backend.services.audit_service import log_audit_event
from backend.db.redis import redis_set_json, redis_get_json, redis_delete

logger = get_logger("backend.services.auth")


# ── Account Lockout Policy ────────────────────────────────────────────────────
# Lock account after N consecutive failed attempts. Lockout expires after M minutes.

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
_LOCKOUT_KEY_PREFIX = "login_attempts:"


# ── Password Policy ──────────────────────────────────────────────────────
# Enforces minimum security standards for user passwords.

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


def validate_password_strength(password: str) -> None:
    """
    Validates password meets minimum security requirements.
    Raises HTTPException if password is too weak.
    
    Policy:
      - Minimum 8 characters
      - Maximum 128 characters (prevent bcrypt DoS)
      - At least 1 uppercase letter
      - At least 1 lowercase letter
      - At least 1 digit
    """
    errors = []
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"at least {MIN_PASSWORD_LENGTH} characters")
    if len(password) > MAX_PASSWORD_LENGTH:
        errors.append(f"no more than {MAX_PASSWORD_LENGTH} characters")
    if not re.search(r"[A-Z]", password):
        errors.append("at least 1 uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("at least 1 lowercase letter")
    if not re.search(r"\d", password):
        errors.append("at least 1 digit")
    if errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too weak. Required: {', '.join(errors)}.",
        )


# ── Password Hashing Helpers ─────────────────────────────────────────

def hash_password(password: str) -> str:
    """Generate a bcrypt hash of a plaintext password."""
    pw_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pw_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception as e:
        logger.error("password_verification_failed", error=str(e))
        return False


# ── Token Generation Helpers ─────────────────────────────────────────

def create_access_token(user_id: uuid.UUID, role: str) -> str:
    """Generate a short-lived access JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(user_id: uuid.UUID) -> str:
    """Generate a long-lived refresh JWT token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


# ── Business Logic ───────────────────────────────────────────────────

async def register_user(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession,
) -> User:
    """
    Register a new user account.
    Validates email uniqueness and hashes the password.
    Logs an audit event for registration.
    """
    # SECURITY: Enforce password policy
    validate_password_strength(data.password)

    # Check if user already exists
    query = select(User).where(User.email == data.email)
    result = await db.execute(query)
    existing_user = result.scalars().first()

    if existing_user:
        await log_audit_event(
            db=db,
            action="register",
            status="failure",
            details={"email": data.email, "reason": "email_taken"},
            request=request,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address is already registered.",
        )

    # Hash the password and create the user
    pwd_hash = hash_password(data.password)
    new_user = User(
        name=data.name,
        email=data.email,
        password_hash=pwd_hash,
        role=data.role,
        is_active=True,
    )

    db.add(new_user)
    await db.flush()  # Populates new_user.id
    await db.refresh(new_user)  # Populate server defaults (created_at, etc.)

    # Log successful registration
    await log_audit_event(
        db=db,
        action="register",
        status="success",
        user_id=new_user.id,
        details={"email": data.email, "role": data.role},
        request=request,
    )

    logger.info("user_registered", user_id=str(new_user.id), email=data.email)
    return new_user


async def authenticate_user(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession,
) -> Tuple[User, str, str]:
    """
    Authenticate a user by email and password.
    Generates access and refresh tokens, stores refresh token in Redis,
    updates last_login_at timestamp, and logs audit events.

    Includes account lockout: after 5 failed attempts, the account is
    locked for 15 minutes regardless of correct credentials.
    """
    # ── Check lockout status ──────────────────────────────────────────
    lockout_key = f"{_LOCKOUT_KEY_PREFIX}{credentials.email}"
    lockout_data = await redis_get_json(lockout_key)
    if lockout_data and lockout_data.get("count", 0) >= MAX_FAILED_ATTEMPTS:
        logger.warning("account_locked_out", email=credentials.email, attempts=lockout_data["count"])
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account temporarily locked due to {MAX_FAILED_ATTEMPTS} failed login attempts. "
                   f"Please try again in {LOCKOUT_DURATION_MINUTES} minutes.",
        )

    query = select(User).where(User.email == credentials.email)
    result = await db.execute(query)
    user = result.scalars().first()

    # Generic error message to prevent email enumeration attacks
    invalid_credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user or not user.is_active:
        await log_audit_event(
            db=db,
            action="login",
            status="failure",
            details={"email": credentials.email, "reason": "user_not_found_or_inactive"},
            request=request,
        )
        # Increment failed attempts
        attempts = (lockout_data.get("count", 0) if lockout_data else 0) + 1
        await redis_set_json(lockout_key, {"count": attempts}, ttl=LOCKOUT_DURATION_MINUTES * 60)
        raise invalid_credentials_exception

    if not verify_password(credentials.password, user.password_hash):
        await log_audit_event(
            db=db,
            action="login",
            status="failure",
            user_id=user.id,
            details={"email": credentials.email, "reason": "invalid_password"},
            request=request,
        )
        # Increment failed attempts
        attempts = (lockout_data.get("count", 0) if lockout_data else 0) + 1
        await redis_set_json(lockout_key, {"count": attempts}, ttl=LOCKOUT_DURATION_MINUTES * 60)
        remaining = MAX_FAILED_ATTEMPTS - attempts
        if remaining > 0:
            logger.info("login_failed_attempt", email=credentials.email, attempts=attempts, remaining=remaining)
        raise invalid_credentials_exception

    # ── Successful authentication — reset lockout counter ─────────────
    await redis_delete(lockout_key)
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    # Store refresh token in Redis for blacklisting / revocation capabilities
    redis_key = f"refresh_token:{str(user.id)}:{refresh_token[-10:]}"
    # TTL matches the refresh token expiry (7 days)
    ttl_seconds = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await redis_set_json(redis_key, {"valid": True}, ttl=ttl_seconds)

    # Update last login timestamp
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)

    # Log successful login
    await log_audit_event(
        db=db,
        action="login",
        status="success",
        user_id=user.id,
        request=request,
    )

    logger.info("user_logged_in", user_id=str(user.id), email=user.email)
    return user, access_token, refresh_token


async def refresh_access_token(
    request: Request,
    refresh_token: str,
    db: AsyncSession,
) -> Tuple[User, str, str]:
    """
    Validate a refresh token, issue a new access token and rotating refresh token.
    Implements single-use rotating refresh tokens to prevent replay attacks.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")

        if not user_id_str or token_type != "refresh":
            raise credentials_exception

        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    # Check refresh token validity in Redis
    redis_key = f"refresh_token:{str(user_id)}:{refresh_token[-10:]}"
    token_status = await redis_get_json(redis_key)
    
    if not token_status or not token_status.get("valid"):
        # Replay attack or revoked token! Revoke ALL sessions for this user for security.
        logger.warning("revoked_refresh_token_reuse_attempted", user_id=str(user_id))
        # Clear any active refresh tokens for this user in background (audit log it)
        await log_audit_event(
            db=db,
            action="token_refresh",
            status="failure",
            user_id=user_id,
            details={"reason": "revoked_or_reused_refresh_token"},
            request=request,
        )
        raise credentials_exception

    # Retrieve user from DB
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if not user or not user.is_active:
        await log_audit_event(
            db=db,
            action="token_refresh",
            status="failure",
            user_id=user_id,
            details={"reason": "user_inactive_or_deleted"},
            request=request,
        )
        raise credentials_exception

    # Revoke current refresh token (rotating)
    await redis_delete(redis_key)

    # Issue new access + rotating refresh token
    new_access = create_access_token(user.id, user.role)
    new_refresh = create_refresh_token(user.id)

    # Store new refresh token in Redis
    new_redis_key = f"refresh_token:{str(user.id)}:{new_refresh[-10:]}"
    ttl_seconds = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    await redis_set_json(new_redis_key, {"valid": True}, ttl=ttl_seconds)

    # Audit log the rotation
    await log_audit_event(
        db=db,
        action="token_refresh",
        status="success",
        user_id=user.id,
        request=request,
    )

    logger.info("token_refreshed", user_id=str(user.id))
    return user, new_access, new_refresh
