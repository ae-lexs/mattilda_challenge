"""Structured logging configuration using structlog.

Provides JSON output for production and colored console output for development.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog

from mattilda_challenge.infrastructure.observability.request_id import get_request_id


def add_request_id(
    logger: structlog.types.WrappedLogger,  # noqa: ARG001
    method_name: str,  # noqa: ARG001
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Processor to add request_id to every log entry."""
    request_id = get_request_id()
    if request_id:
        event_dict["request_id"] = request_id
    return event_dict


def configure_logging(*, debug: bool = False) -> None:
    """
    Configure structlog for the application.

    Args:
        debug: If True, use colored console output. If False, use JSON.
    """
    # Shared processors for all environments
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    if debug:
        # Development: colored console output
        processors: list[Any] = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output
        processors = [
            *shared_processors,
            structlog.processors.EventRenamer("message"),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if debug else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """
    Get a configured structlog logger.

    Args:
        name: Optional logger name (typically __name__)

    Returns:
        Configured bound logger
    """
    return structlog.get_logger(name)
