"""School repository adapter implementations."""

from mattilda_challenge.infrastructure.adapters.school_repository.in_memory import (
    InMemorySchoolRepository,
)
from mattilda_challenge.infrastructure.adapters.school_repository.postgres import (
    PostgresSchoolRepository,
)

__all__ = [
    "InMemorySchoolRepository",
    "PostgresSchoolRepository",
]
