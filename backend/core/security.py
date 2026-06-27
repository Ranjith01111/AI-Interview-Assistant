"""
Security Utilities — CORS, API-Key verification, JWT Auth, and RBAC Guards.
"""

import uuid
from typing import List, Callable, Optional
import jwt
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.session import get_db
from backend.models.user import User, UserRole

logger = get_logger("backend.core.security")


# ── CORS Configuration ────────────────────────────────────────────────

def configure_cors(app: Starlette) -> None:
    """
    Attach CORS middleware to the FastAPI/Starlette application.

    In development (DEBUG=True) allowed origins are set explicitly
    (NOT wildcard "*") to safely support credentials.
    In production the origins are restricted to ALLOWED_ORIGINS.
    """
    # SECURITY FIX: Never use allow_origins=["*"] with allow_credentials=True
    # Browsers reject Set-Cookie headers when origin is wildcard.
    # In DEBUG mode, use the explicit ALLOWED_ORIGINS list (which defaults to
    # localhost:8501, localhost:3000, localhost:5173).
    origins = settings.allowed_origins_list
    if settings.DEBUG and not origins:
        origins = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )


# ── API-Key Header Guard (Legacy/Internal) ────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str = Security(_api_key_header),
) -> str:
    """
    Dependency that validates an X-API-Key header against SECRET_KEY.

    Usage (on a per-route basis):
        @router.get("/admin/…", dependencies=[Depends(verify_api_key)])
    """
    if api_key is None or api_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key.",
        )
    return api_key


# ── Enterprise JWT Authentication & RBAC Dependencies ───────────────

# Define the OAuth2 bearer flow scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency that extracts, decodes, and validates a JWT access token,
    then retrieves the corresponding user from the database.
    In debug mode, it falls back to a default dev user if no token is provided.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        if settings.DEBUG:
            logger.warning("debug_fallback_user_created", note="Auth bypassed in DEBUG mode — NEVER use in production")
            # Fallback to dev user in local debug mode
            query = select(User).where(User.email == "dev@example.com")
            result = await db.execute(query)
            user = result.scalars().first()
            if not user:
                user = User(
                    name="Dev User",
                    email="dev@example.com",
                    password_hash="dev-hash-not-used",
                    role=UserRole.CANDIDATE.value,  # SECURITY: Dev user is CANDIDATE only, never admin
                    is_active=True
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
            return user
        raise credentials_exception

    try:
        # Decode access token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        token_type: str = payload.get("type")

        if not user_id_str or token_type != "access":
            raise credentials_exception

        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    # Query user from DB
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that ensures the authenticated user is active.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact support.",
        )
    return current_user


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    """
    Role-Based Access Control (RBAC) route guard.
    Returns a dependency function that enforces specific user roles.
    
    Usage:
        @router.get("/admin-only", dependencies=[Depends(require_role(UserRole.ADMIN))])
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if current_user.role not in [role.value for role in allowed_roles]:
            logger.warning(
                "unauthorized_role_access_attempted",
                user_id=str(current_user.id),
                user_role=current_user.role,
                allowed_roles=[role.value for role in allowed_roles],
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permissions to perform this action.",
            )
        return current_user

    return role_checker
