from __future__ import annotations

from abc import ABC, abstractmethod

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import SchoolFilters
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId


class SchoolRepository(ABC):
    """
    Port for school data access.

    All implementations must inherit from this class and implement
    all abstract methods. Repositories never call commit() - that's
    owned by UnitOfWork.
    """

    @abstractmethod
    async def get_by_id(
        self,
        school_id: SchoolId,
        for_update: bool = False,
    ) -> School | None:
        """
        Get school by ID or None if not found.

        Args:
            school_id: Unique school identifier
            for_update: If True, acquire row lock (SELECT ... FOR UPDATE)

        Returns:
            School entity or None if not found
        """
        ...

    @abstractmethod
    async def save(self, school: School) -> School:
        """
        Save school entity to persistence.

        Performs upsert: inserts if new, updates if exists.
        Calls flush() to write to database within current transaction.

        Args:
            school: School entity to save

        Returns:
            Saved school (may have refreshed fields)
        """
        ...

    @abstractmethod
    async def find(
        self,
        filters: SchoolFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[School]:
        """
        Find schools matching filters with pagination.

        Args:
            filters: Filter criteria (all optional)
            pagination: Offset and limit
            sort: Sort field and direction

        Returns:
            Page containing matching schools and metadata
        """
        ...

    @abstractmethod
    async def delete(self, school_id: SchoolId) -> None:
        """
        Delete a school by ID.

        Args:
            school_id: Unique school identifier

        Note:
            Does not commit - UnitOfWork handles transaction.
            Caller should verify school exists before calling.
        """
        ...
