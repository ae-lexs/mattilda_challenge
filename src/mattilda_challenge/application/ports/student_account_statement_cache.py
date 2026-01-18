from __future__ import annotations

from abc import ABC, abstractmethod

from mattilda_challenge.application.dtos import (
    StudentAccountStatement,
)
from mattilda_challenge.domain.value_objects import StudentId


class StudentAccountStatementCache(ABC):
    """
    Port for caching student account statements.

    Contract:
    - get() returns None on cache miss (not found or expired)
    - get() returns None on cache failure (fail-open)
    - set() is best-effort (failures are logged, not raised)
    - Implementations handle serialization internally
    """

    @abstractmethod
    async def get(self, student_id: StudentId) -> StudentAccountStatement | None:
        """
        Retrieve cached student account statement.

        Args:
            student_id: Student identifier

        Returns:
            Cached statement or None if not found/expired/error
        """
        ...

    @abstractmethod
    async def set(self, statement: StudentAccountStatement) -> None:
        """
        Cache student account statement with TTL.

        Args:
            statement: Account statement to cache

        Note:
            Failures are logged but not raised (fail-open).
            TTL is configured in the implementation.
        """
        ...
