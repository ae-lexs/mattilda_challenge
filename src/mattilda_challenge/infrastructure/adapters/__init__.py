"""Infrastructure adapters."""

from mattilda_challenge.infrastructure.adapters.time_provider import (
    FixedTimeProvider,
    SystemTimeProvider,
)

__all__ = [
    "FixedTimeProvider",
    "SystemTimeProvider",
]
