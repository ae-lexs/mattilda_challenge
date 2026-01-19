"""Health check endpoints."""

from __future__ import annotations

import time
from collections.abc import Awaitable
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Response, status
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.config import get_settings
from mattilda_challenge.entrypoints.http.dependencies import RedisDep, SessionDep
from mattilda_challenge.entrypoints.http.dtos import (
    DependencyHealth,
    HealthResponse,
    HealthStatus,
    LivenessResponse,
)
from mattilda_challenge.infrastructure.observability import get_logger

router = APIRouter(tags=["Health"])
logger = get_logger(__name__)


async def check_database(session: AsyncSession) -> DependencyHealth:
    """Check database connectivity."""
    start = time.perf_counter()
    try:
        await session.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000
        return DependencyHealth(
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
        )
    except Exception as e:
        logger.warning("database_health_check_failed", error=str(e))
        return DependencyHealth(
            status=HealthStatus.UNHEALTHY,
            error=str(e),
        )


async def _ping_redis(redis: Redis) -> bool:
    """Ping redis with proper async handling."""
    result = redis.ping()
    if hasattr(result, "__await__"):
        return await cast(Awaitable[bool], result)
    return result


async def check_redis(redis: Redis) -> DependencyHealth:
    """Check Redis connectivity."""
    start = time.perf_counter()
    try:
        await _ping_redis(redis)
        latency_ms = (time.perf_counter() - start) * 1000
        return DependencyHealth(
            status=HealthStatus.HEALTHY,
            latency_ms=round(latency_ms, 2),
        )
    except Exception as e:
        logger.warning("redis_health_check_failed", error=str(e))
        return DependencyHealth(
            status=HealthStatus.UNHEALTHY,
            error=str(e),
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check with dependency status",
    description="Returns application health status including all dependencies.",
)
async def health_check(
    response: Response,
    session: SessionDep,
    redis: RedisDep,
) -> HealthResponse:
    """
    Combined health check endpoint.

    Checks:
    - Database connectivity (PostgreSQL)
    - Cache connectivity (Redis)

    Returns 200 if all healthy, 503 if any dependency is unhealthy.
    """
    settings = get_settings()

    # Check all dependencies
    db_health = await check_database(session)
    redis_health = await check_redis(redis)

    dependencies = {
        "database": db_health,
        "redis": redis_health,
    }

    # Determine overall status
    all_healthy = all(
        dep.status == HealthStatus.HEALTHY for dep in dependencies.values()
    )
    overall_status = HealthStatus.HEALTHY if all_healthy else HealthStatus.UNHEALTHY

    # Set HTTP status code based on health
    if overall_status != HealthStatus.HEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
        dependencies=dependencies,
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    summary="Liveness probe",
    description="Simple check that the application process is running.",
)
async def liveness() -> LivenessResponse:
    """
    Liveness probe endpoint.

    Returns 200 if the application is running. Used by orchestrators
    to determine if the process should be restarted.

    Note: Does NOT check external dependencies (by design).
    """
    return LivenessResponse()


@router.get(
    "/health/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
    description="Check if the application is ready to receive traffic.",
)
async def readiness(
    response: Response,
    session: SessionDep,
    redis: RedisDep,
) -> HealthResponse:
    """
    Readiness probe endpoint.

    Returns 200 if the application can handle requests (all dependencies
    are available). Returns 503 if not ready.

    Note: Same checks as /health, but semantically indicates "can accept traffic".
    """
    return await health_check(response, session, redis)
