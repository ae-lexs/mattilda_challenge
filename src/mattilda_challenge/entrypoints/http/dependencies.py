"""FastAPI dependency injection factories.

Provides factory functions for injecting dependencies into route handlers.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable
from typing import Annotated, cast

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.ports import (
    SchoolAccountStatementCache,
    StudentAccountStatementCache,
)
from mattilda_challenge.application.ports.time_provider import TimeProvider
from mattilda_challenge.application.ports.unit_of_work import UnitOfWork
from mattilda_challenge.config import Settings, get_settings
from mattilda_challenge.infrastructure.adapters.school_account_statement_cache import (
    NullSchoolAccountStatementCache,
    RedisSchoolAccountStatementCache,
)
from mattilda_challenge.infrastructure.adapters.student_account_statement_cache import (
    NullStudentAccountStatementCache,
    RedisStudentAccountStatementCache,
)
from mattilda_challenge.infrastructure.adapters.time_provider import (
    SystemTimeProvider,
)
from mattilda_challenge.infrastructure.adapters.unit_of_work import PostgresUnitOfWork
from mattilda_challenge.infrastructure.postgres.database import get_session
from mattilda_challenge.infrastructure.redis.client import get_redis_client


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """Get database session from pool."""
    async for session in get_session():
        yield session


async def get_redis() -> AsyncGenerator[Redis]:
    """Get Redis client."""
    async for redis in get_redis_client():
        yield redis


def get_time_provider() -> TimeProvider:
    """Get time provider."""
    return SystemTimeProvider()


async def get_unit_of_work(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AsyncGenerator[UnitOfWork]:
    """Get Unit of Work with database session."""
    uow = PostgresUnitOfWork(session)
    yield uow


async def _ping_redis(redis: Redis) -> bool:
    """Ping redis with proper async handling."""
    result = redis.ping()
    if hasattr(result, "__await__"):
        return await cast(Awaitable[bool], result)
    return result


async def get_student_account_statement_cache(
    redis: Annotated[Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StudentAccountStatementCache:
    """Get student account statement cache."""
    _ = settings  # Settings used by Redis cache internally
    try:
        await _ping_redis(redis)
        return RedisStudentAccountStatementCache(redis)
    except Exception:
        # Fall back to null cache if Redis is unavailable
        return NullStudentAccountStatementCache()


async def get_school_account_statement_cache(
    redis: Annotated[Redis, Depends(get_redis)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SchoolAccountStatementCache:
    """Get school account statement cache."""
    _ = settings  # Settings used by Redis cache internally
    try:
        await _ping_redis(redis)
        return RedisSchoolAccountStatementCache(redis)
    except Exception:
        # Fall back to null cache if Redis is unavailable
        return NullSchoolAccountStatementCache()


# Type aliases for cleaner route signatures
SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]
TimeProviderDep = Annotated[TimeProvider, Depends(get_time_provider)]
UnitOfWorkDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]
StudentCacheDep = Annotated[
    StudentAccountStatementCache, Depends(get_student_account_statement_cache)
]
SchoolCacheDep = Annotated[
    SchoolAccountStatementCache, Depends(get_school_account_statement_cache)
]
SettingsDep = Annotated[Settings, Depends(get_settings)]
