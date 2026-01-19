"""Health check DTOs."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Health check status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class DependencyHealth(BaseModel):
    """Health status of a single dependency."""

    status: HealthStatus
    latency_ms: float | None = Field(
        default=None,
        description="Response time in milliseconds",
    )
    error: str | None = Field(
        default=None,
        description="Error message if unhealthy",
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: HealthStatus
    version: str = Field(description="Application version")
    timestamp: datetime = Field(description="Check timestamp (UTC)")
    dependencies: dict[str, DependencyHealth] = Field(
        default_factory=dict,
        description="Status of external dependencies",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": "2024-01-20T15:00:00Z",
                "dependencies": {
                    "database": {"status": "healthy", "latency_ms": 5.2},
                    "redis": {"status": "healthy", "latency_ms": 1.8},
                },
            }
        }
    }


class LivenessResponse(BaseModel):
    """Simple liveness response."""

    status: Literal["alive"] = "alive"
