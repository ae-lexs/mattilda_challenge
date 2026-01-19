from __future__ import annotations

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import StudentFilters
from mattilda_challenge.application.ports import StudentRepository
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId


class InMemoryStudentRepository(StudentRepository):
    """
    In-memory implementation of StudentRepository for testing.

    Stores entities in a dictionary. Does not persist between test runs.
    Used in unit tests to verify use case behavior without database.
    """

    def __init__(self) -> None:
        """Initialize empty repository."""
        self._students: dict[StudentId, Student] = {}

    async def get_by_id(
        self,
        student_id: StudentId,
        for_update: bool = False,  # noqa: ARG002
    ) -> Student | None:
        """
        Get student by ID.

        Note: for_update is ignored in memory implementation
        (no concurrent access in unit tests).
        """
        return self._students.get(student_id)

    async def save(self, student: Student) -> Student:
        """Save student to in-memory storage."""
        self._students[student.id] = student
        return student

    async def find(
        self,
        filters: StudentFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Student]:
        """Find students with filtering, sorting, and pagination."""
        # Filter
        items = list(self._students.values())
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

    async def exists_by_email(self, email: str) -> bool:
        """Check if a student with given email already exists."""
        return any(student.email == email for student in self._students.values())

    async def count_by_school(self, school_id: SchoolId) -> int:
        """Count students in a school."""
        count = 0
        for student in self._students.values():
            if student.school_id == school_id:
                count += 1
        return count

    def _apply_filters(
        self,
        items: list[Student],
        filters: StudentFilters,
    ) -> list[Student]:
        """Apply filter criteria to student list."""
        result = items

        if filters.school_id is not None:
            result = [s for s in result if s.school_id.value == filters.school_id]

        if filters.status is not None:
            result = [s for s in result if s.status.value == filters.status]

        if filters.email is not None:
            result = [s for s in result if s.email == filters.email]

        return result

    def _apply_sort(
        self,
        items: list[Student],
        sort: SortParams,
    ) -> list[Student]:
        """Apply sorting to student list."""
        sort_key_map = {
            "created_at": lambda s: (s.created_at, s.id.value),
            "enrollment_date": lambda s: (s.enrollment_date, s.id.value),
            "first_name": lambda s: (s.first_name.lower(), s.id.value),
            "last_name": lambda s: (s.last_name.lower(), s.id.value),
            "email": lambda s: (s.email.lower(), s.id.value),
            "status": lambda s: (s.status.value, s.id.value),
        }

        key_func = sort_key_map.get(sort.sort_by, sort_key_map["created_at"])
        reverse = sort.sort_order == "desc"

        return sorted(items, key=key_func, reverse=reverse)

    async def delete(self, student_id: StudentId) -> None:
        """Delete student by ID."""
        self._students.pop(student_id, None)

    # Test helper methods (not part of port interface)

    def clear(self) -> None:
        """Clear all stored students (test utility)."""
        self._students.clear()

    def add(self, student: Student) -> None:
        """Add student directly (test utility for setup)."""
        self._students[student.id] = student
