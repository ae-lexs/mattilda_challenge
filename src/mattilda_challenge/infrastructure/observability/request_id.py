"""Request ID middleware for request tracing.

Provides request-scoped context for logging and correlation.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Request-scoped context variable
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_ctx.get()


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to extract or generate X-Request-ID header.

    - Extracts X-Request-ID from incoming request headers
    - Generates UUID4 if not present
    - Stores in contextvars for access anywhere in request lifecycle
    - Adds to response headers for client correlation
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Process request with request ID context."""
        # Extract or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in context for access by loggers
        token = request_id_ctx.set(request_id)

        try:
            response = await call_next(request)
            # Echo request ID in response headers
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_ctx.reset(token)
