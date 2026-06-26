"""
Redis Connection Pool & Helpers

Provides:
  • `redis_pool`   — the shared aioredis connection pool
  • `get_redis()`  — FastAPI dependency
  • JSON get/set/delete helpers with TTL
"""

import json
import pickle
from typing import Any, Optional

import redis.asyncio as aioredis

from backend.core.config import settings

# ── Connection pool (created lazily) ─────────────────────────────────
_redis_client: Optional[aioredis.Redis] = None


async def init_redis() -> aioredis.Redis:
    """Create and return the global Redis client."""
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=False,  # we handle encoding ourselves
        max_connections=20,
    )
    return _redis_client


async def close_redis() -> None:
    """Gracefully shut down the Redis connection pool."""
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency — yields the Redis client."""
    if _redis_client is None:
        await init_redis()
    return _redis_client


# ── JSON helpers ─────────────────────────────────────────────────────

async def redis_set_json(
    key: str,
    value: Any,
    ttl: int = settings.REDIS_SESSION_TTL,
) -> None:
    """Serialize *value* to JSON and store with TTL (seconds)."""
    client = await get_redis()
    await client.set(key, json.dumps(value, default=str), ex=ttl)


async def redis_get_json(key: str) -> Optional[Any]:
    """Retrieve and deserialize a JSON value, or None if missing."""
    client = await get_redis()
    raw = await client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def redis_delete(key: str) -> None:
    """Delete a key."""
    client = await get_redis()
    await client.delete(key)


# ── Pickle helpers (for serializable objects) ────────────────────────

async def redis_set_pickle(
    key: str,
    obj: Any,
    ttl: int = settings.REDIS_SESSION_TTL,
) -> None:
    """Pickle-serialize *obj* and store with TTL."""
    client = await get_redis()
    await client.set(key, pickle.dumps(obj), ex=ttl)


async def redis_get_pickle(key: str) -> Optional[Any]:
    """Retrieve and unpickle an object, or None if missing."""
    client = await get_redis()
    raw = await client.get(key)
    if raw is None:
        return None
    return pickle.loads(raw)


# ── Raw bytes helpers (for FAISS / objects with unpicklable C extensions) ──
# FAISS IndexFlat holds _thread.RLock objects internally which cannot be
# serialized with pickle.  Use FAISS's own serialize_to_bytes() instead.

async def redis_set_bytes(
    key: str,
    data: bytes,
    ttl: int = settings.REDIS_SESSION_TTL,
) -> None:
    """Store raw bytes with TTL."""
    client = await get_redis()
    await client.set(key, data, ex=ttl)


async def redis_get_bytes(key: str) -> Optional[bytes]:
    """Retrieve raw bytes, or None if missing."""
    client = await get_redis()
    return await client.get(key)


async def redis_ping() -> bool:
    """Return True if Redis is reachable."""
    try:
        client = await get_redis()
        return await client.ping()
    except Exception:
        return False
