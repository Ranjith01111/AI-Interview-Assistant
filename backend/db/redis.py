"""
Redis Connection Pool & Helpers — RESILIENT VERSION

GUARANTEES:
  • App NEVER crashes if Redis is down
  • All redis_* functions return None/no-op gracefully when disconnected
  • Automatic reconnection attempts on each call
  • Startup doesn't block or crash if Redis is unreachable
"""

import json
import pickle
from typing import Any, Optional

from backend.core.config import settings

try:
    import redis.asyncio as aioredis
    HAS_REDIS_LIB = True
except ImportError:
    HAS_REDIS_LIB = False
    aioredis = None

from backend.core.logging import get_logger

logger = get_logger("backend.db.redis")

# ── Connection pool (created lazily) ─────────────────────────────────────────
_redis_client: Optional[Any] = None
_redis_available: bool = False


async def init_redis() -> Optional[Any]:
    """Create the global Redis client. Never raises — returns None on failure."""
    global _redis_client, _redis_available

    if not HAS_REDIS_LIB:
        logger.warning("redis_library_not_installed", hint="pip install redis[hiredis]")
        _redis_available = False
        return None

    try:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            max_connections=20,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
        # Test connection
        await _redis_client.ping()
        _redis_available = True
        logger.info("redis_connected", url=settings.REDIS_URL)
        return _redis_client
    except Exception as e:
        logger.warning("redis_init_failed", error=str(e), hint="App running without cache")
        _redis_available = False
        _redis_client = None
        return None


async def close_redis() -> None:
    """Gracefully shut down the Redis connection pool."""
    global _redis_client, _redis_available
    if _redis_client:
        try:
            await _redis_client.aclose()
        except Exception:
            pass
        _redis_client = None
    _redis_available = False


async def get_redis() -> Optional[Any]:
    """Get Redis client. Returns None if not available (never raises)."""
    global _redis_client, _redis_available
    if _redis_client and _redis_available:
        return _redis_client
    # Try to reconnect (lazy init)
    if not _redis_client:
        await init_redis()
    return _redis_client if _redis_available else None


async def _safe_client() -> Optional[Any]:
    """Internal: get client or None. Handles disconnection detection."""
    global _redis_available
    client = await get_redis()
    if not client:
        return None
    # Quick availability check (don't ping every time — trust the flag)
    return client


# ══════════════════════════════════════════════════════════════════════════════
# JSON helpers — ALL return None gracefully when Redis is down
# ══════════════════════════════════════════════════════════════════════════════

async def redis_set_json(
    key: str,
    value: Any,
    ttl: int = settings.REDIS_SESSION_TTL,
) -> None:
    """Serialize value to JSON and store. No-op if Redis unavailable."""
    client = await _safe_client()
    if not client:
        return
    try:
        await client.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception as e:
        logger.debug("redis_set_json_failed", key=key, error=str(e))
        _mark_unavailable()


async def redis_get_json(key: str) -> Optional[Any]:
    """Retrieve and deserialize JSON. Returns None if Redis unavailable or key missing."""
    client = await _safe_client()
    if not client:
        return None
    try:
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.debug("redis_get_json_failed", key=key, error=str(e))
        _mark_unavailable()
        return None


async def redis_delete(key: str) -> None:
    """Delete a key. No-op if Redis unavailable."""
    client = await _safe_client()
    if not client:
        return
    try:
        await client.delete(key)
    except Exception as e:
        logger.debug("redis_delete_failed", key=key, error=str(e))
        _mark_unavailable()


# ══════════════════════════════════════════════════════════════════════════════
# Pickle helpers — ALL return None gracefully when Redis is down
# ══════════════════════════════════════════════════════════════════════════════

async def redis_set_pickle(
    key: str,
    obj: Any,
    ttl: int = settings.REDIS_SESSION_TTL,
) -> None:
    """Pickle-serialize obj and store. No-op if Redis unavailable."""
    client = await _safe_client()
    if not client:
        return
    try:
        await client.set(key, pickle.dumps(obj), ex=ttl)
    except Exception as e:
        logger.debug("redis_set_pickle_failed", key=key, error=str(e))
        _mark_unavailable()


async def redis_get_pickle(key: str) -> Optional[Any]:
    """Retrieve and unpickle. Returns None if Redis unavailable."""
    client = await _safe_client()
    if not client:
        return None
    try:
        raw = await client.get(key)
        if raw is None:
            return None
        return pickle.loads(raw)
    except Exception as e:
        logger.debug("redis_get_pickle_failed", key=key, error=str(e))
        _mark_unavailable()
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Raw bytes helpers
# ══════════════════════════════════════════════════════════════════════════════

async def redis_set_bytes(
    key: str,
    data: bytes,
    ttl: int = settings.REDIS_SESSION_TTL,
) -> None:
    """Store raw bytes. No-op if Redis unavailable."""
    client = await _safe_client()
    if not client:
        return
    try:
        await client.set(key, data, ex=ttl)
    except Exception as e:
        logger.debug("redis_set_bytes_failed", key=key, error=str(e))
        _mark_unavailable()


async def redis_get_bytes(key: str) -> Optional[bytes]:
    """Retrieve raw bytes. Returns None if Redis unavailable."""
    client = await _safe_client()
    if not client:
        return None
    try:
        return await client.get(key)
    except Exception as e:
        logger.debug("redis_get_bytes_failed", key=key, error=str(e))
        _mark_unavailable()
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Health check
# ══════════════════════════════════════════════════════════════════════════════

async def redis_ping() -> bool:
    """Return True if Redis is reachable."""
    client = await _safe_client()
    if not client:
        return False
    try:
        return await client.ping()
    except Exception:
        _mark_unavailable()
        return False


def _mark_unavailable():
    """Mark Redis as unavailable. Will try reconnecting on next call."""
    global _redis_available, _redis_client
    _redis_available = False
    _redis_client = None

from contextlib import asynccontextmanager

@asynccontextmanager
async def redis_lock(lock_name: str, timeout: int = 10, sleep: float = 0.1):
    """
    Mutex Lock to prevent cache race conditions.
    Yields True if lock acquired, False otherwise (or if Redis is down).
    """
    client = await _safe_client()
    if not client:
        yield False
        return

    # Use redis.lock
    lock = client.lock(lock_name, timeout=timeout, sleep=sleep)
    acquired = await lock.acquire(blocking=True)
    try:
        yield acquired
    finally:
        if acquired:
            try:
                await lock.release()
            except Exception:
                pass
