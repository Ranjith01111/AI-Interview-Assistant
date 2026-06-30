"""
SQLAlchemy Async Session Factory

Provides:
  • `async_engine`       — the single AsyncEngine for the app
  • `AsyncSessionLocal`  — session factory
  • `get_db()`           — FastAPI dependency that yields a session
  • `init_db()`          — creates tables (dev-only; use Alembic in prod)
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.core.config import settings
from backend.db.base import Base
from sqlalchemy import text
from backend.core.resilience import ServiceUnavailableError
import asyncio
import logging

logger = logging.getLogger("backend.db.session")

# ── Engine ───────────────────────────────────────────────────────────
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,            # SQL logging in dev
    pool_size=20,                   # connection pool
    max_overflow=10,
    pool_pre_ping=True,             # verify connections before checkout
    pool_recycle=3600,              # recycle connections every hour
    connect_args={"command_timeout": 15}, # Prevent queries from hanging forever
)

# ── Session factory ──────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── FastAPI dependency ───────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    Yields an async SQLAlchemy session for a single request.
    Includes a connection liveness check and retry logic for resilience.
    """
    session = AsyncSessionLocal()
    try:
        # Liveness check with retry
        for attempt in range(3):
            try:
                await session.execute(text("SELECT 1"))
                break
            except Exception as e:
                if attempt == 2:
                    logger.error("db_liveness_check_failed", error=str(e))
                    raise ServiceUnavailableError("Database connection unavailable", e)
                logger.warning("db_liveness_check_retry", attempt=attempt + 1, error=str(e))
                await asyncio.sleep(0.1 * (2 ** attempt))

        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


# ── Bootstrap helper (development only) ──────────────────────────────
async def init_db() -> None:
    """
    Create all tables defined on `Base.metadata`.

    ⚠️  In production, use Alembic migrations instead.
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the connection pool (call on shutdown)."""
    await async_engine.dispose()
