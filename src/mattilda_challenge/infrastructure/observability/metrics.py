"""Prometheus metrics configuration for FastAPI.

Uses prometheus-fastapi-instrumentator for automatic HTTP metrics.
"""

from __future__ import annotations

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator, metrics


def setup_metrics(app: FastAPI) -> Instrumentator:
    """
    Configure Prometheus metrics for FastAPI application.

    Args:
        app: FastAPI application instance

    Returns:
        Configured instrumentator (for testing access)
    """
    instrumentator = Instrumentator(
        should_group_status_codes=True,  # Group 2xx, 3xx, etc.
        should_ignore_untemplated=True,  # Ignore unmatched routes
        should_respect_env_var=True,  # ENABLE_METRICS env var
        should_instrument_requests_inprogress=True,
        excluded_handlers=[
            "/health",
            "/health/live",
            "/health/ready",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ],
        inprogress_name="http_requests_in_progress",
        inprogress_labels=True,
    )

    # Add default metrics
    instrumentator.add(
        metrics.default(
            metric_namespace="mattilda",
            metric_subsystem="api",
        )
    )

    # Instrument app and expose /metrics endpoint
    instrumentator.instrument(app).expose(
        app,
        endpoint="/metrics",
        include_in_schema=False,  # Hide from OpenAPI docs
        should_gzip=True,
    )

    return instrumentator
