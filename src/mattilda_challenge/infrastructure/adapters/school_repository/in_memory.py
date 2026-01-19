from __future__ import annotations

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import SchoolFilters
from mattilda_challenge.application.ports import SchoolRepository
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId


class InMemorySchoolRepository(SchoolRepository):
    """
    In-memory implementation of SchoolRepository for testing.

    Stores entities in a dictionary. Does not persist between test runs.
    Used in unit tests to verify use case behavior without database.
    """

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._schools: dict[SchoolId, School] = {}

    async def get_by_id(
        self,
        school_id: SchoolId,
        for_update: bool = False,  # noqa: ARG002
    ) -> School | None:
        """
        Get school by ID.

        Note: for_update is ignored in memory implementation
        (no concurrent access in unit tests).
        """
        return self._schools.get(school_id)

    async def save(self, school: School) -> School:
        """Save school to in-memory storage."""
        self._schools[school.id] = school
        return school

    async def find(
        self,
        filters: SchoolFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[School]:
        """Find schools with filtering, sorting, and pagination."""
        # Filter
        items = list(self._schools.values())
        items = self._apply_filters(items, filters)

        # Sort
        items = self._apply_sort(items, sort)

        # Count before pagination
        total = len(items)

        # Paginate
        start = pagination.offset
        end = start + pagination.limit
        items = items[start:end]

        return Page(
            items=tuple(items),
            total=total,
            offset=pagination.offset,
            limit=pagination.limit,
        )

    def _apply_filters(
        self,
        items: list[School],
        filters: SchoolFilters,
    ) -> list[School]:
        """Apply filter criteria to school list."""
        result = items

        if filters.name is not None:
            # Case-insensitive partial match
            name_lower = filters.name.lower()
            result = [s for s in result if name_lower in s.name.lower()]

        return result

    def _apply_sort(
        self,
        items: list[School],
        sort: SortParams,
    ) -> list[School]:
        """Apply sorting to school list."""
        sort_key_map = {
            "created_at": lambda s: (s.created_at, s.id.value),
            "name": lambda s: (s.name.lower(), s.id.value),
        }

        key_func = sort_key_map.get(sort.sort_by, sort_key_map["created_at"])
        reverse = sort.sort_order == "desc"

        return sorted(items, key=key_func, reverse=reverse)

    async def delete(self, school_id: SchoolId) -> None:
        """Delete school by ID."""
        self._schools.pop(school_id, None)

    # Test helper methods (not part of port interface)

    def clear(self) -> None:
        """Clear all stored schools (test utility)."""
        self._schools.clear()

    def add(self, school: School) -> None:
        """Add school directly (test utility for setup)."""
        self._schools[school.id] = school
