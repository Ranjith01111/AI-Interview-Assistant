"""
Health Routes — Application health checks with DB and Redis status.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.session import get_db
from backend.db.redis import redis_ping

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    db: AsyncSession = Depends(get_db),
):
    """
    Comprehensive health check endpoint.

    Verifies:
    - Application is running
    - PostgreSQL is reachable
    - Redis is reachable

    Returns:
        JSON with status of each dependency
    """
    # ── Database check ───────────────────────────────────────────────
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # ── Redis check ──────────────────────────────────────────────────
    redis_ok = await redis_ping()
    redis_status = "connected" if redis_ok else "disconnected"

    # ── Overall ──────────────────────────────────────────────────────
    all_healthy = db_status == "connected" and redis_ok
    overall = "healthy" if all_healthy else "degraded"

    return {
        "status": overall,
        "version": settings.APP_VERSION,
        "model": settings.OPENROUTER_MODEL,
        "embedding_model": settings.OPENROUTER_EMBEDDING_MODEL,
        "database": db_status,
        "redis": redis_status,
    }
