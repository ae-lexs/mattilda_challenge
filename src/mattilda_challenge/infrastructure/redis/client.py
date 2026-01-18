from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from redis.asyncio import ConnectionPool, Redis

from mattilda_challenge.config import get_settings

logger = logging.getLogger(__name__)


# Connection pool (shared across all cache adapters)
_pool: ConnectionPool | None = None


async def get_redis_pool() -> ConnectionPool:
    """
    Get or create Redis connection pool.

    Lazily initializes the pool on first call.
    """
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool.from_url(
            settings.redis_url,  # redis://localhost:6379/0
            max_connections=10,
            decode_responses=True,  # Return strings, not bytes
        )
    return _pool


async def get_redis_client() -> AsyncGenerator[Redis]:
    """
    Dependency injection for Redis client.

    Usage in FastAPI:
        @app.get("/...")
        async def endpoint(
            redis: Redis = Depends(get_redis_client)
        ):
            ...

    Yields:
        Redis client instance from pool
    """
    pool = await get_redis_pool()
    client = Redis(connection_pool=pool)
    try:
        yield client
    finally:
        await client.aclose()


async def close_redis_pool() -> None:
    """
    Close Redis connection pool on application shutdown.

    Call from FastAPI lifespan handler.
    """
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
