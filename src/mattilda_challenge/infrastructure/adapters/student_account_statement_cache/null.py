from __future__ import annotations

from mattilda_challenge.application.dtos import (
    StudentAccountStatement,
)
from mattilda_challenge.application.ports import (
    StudentAccountStatementCache,
)
from mattilda_challenge.domain.value_objects import StudentId


class NullStudentAccountStatementCache(StudentAccountStatementCache):
    """
    No-op cache implementation for testing or disabled cache scenarios.

    Always returns None (cache miss) and discards set operations.
    """

    async def get(self, student_id: StudentId) -> StudentAccountStatement | None:  # noqa: ARG002
        return None

    async def set(self, statement: StudentAccountStatement) -> None:  # noqa: ARG002
        pass
