from __future__ import annotations

from abc import ABC, abstractmethod

from mattilda_challenge.application.dtos import (
    SchoolAccountStatement,
)
from mattilda_challenge.domain.value_objects import SchoolId


class SchoolAccountStatementCache(ABC):
    """
    Port for caching school account statements.

    Same contract as StudentAccountStatementCache.
    """

    @abstractmethod
    async def get(self, school_id: SchoolId) -> SchoolAccountStatement | None:
        """
        Retrieve cached school account statement.

        Args:
            school_id: School identifier

        Returns:
            Cached statement or None if not found/expired/error
        """
        ...

    @abstractmethod
    async def set(self, statement: SchoolAccountStatement) -> None:
        """
        Cache school account statement with TTL.

        Args:
            statement: Account statement to cache

        Note:
            Failures are logged but not raised (fail-open).
        """
        ...
