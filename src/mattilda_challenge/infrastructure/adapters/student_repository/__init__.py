"""Student repository adapter implementations."""

from mattilda_challenge.infrastructure.adapters.student_repository.in_memory import (
    InMemoryStudentRepository,
)
from mattilda_challenge.infrastructure.adapters.student_repository.postgres import (
    PostgresStudentRepository,
)

__all__ = [
    "InMemoryStudentRepository",
    "PostgresStudentRepository",
]
