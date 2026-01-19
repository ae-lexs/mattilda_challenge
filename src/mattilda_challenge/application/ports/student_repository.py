from __future__ import annotations

from abc import ABC, abstractmethod

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import StudentFilters
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId


class StudentRepository(ABC):
    """
    Port for student data access.

    All implementations must inherit from this class and implement
    all abstract methods.
    """

    @abstractmethod
    async def get_by_id(
        self,
        student_id: StudentId,
        for_update: bool = False,
    ) -> Student | None:
        """
        Get student by ID or None if not found.

        Args:
            student_id: Unique student identifier
            for_update: If True, acquire row lock

        Returns:
            Student entity or None if not found
        """
        ...

    @abstractmethod
    async def save(self, student: Student) -> Student:
        """
        Save student entity to persistence.

        Args:
            student: Student entity to save

        Returns:
            Saved student
        """
        ...

    @abstractmethod
    async def find(
        self,
        filters: StudentFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Student]:
        """
        Find students matching filters with pagination.

        Args:
            filters: Filter criteria (school_id, status, email)
            pagination: Offset and limit
            sort: Sort field and direction

        Returns:
            Page containing matching students and metadata
        """
        ...

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if a student with given email already exists.

        Used for uniqueness validation before creating students.

        Args:
            email: Email address to check

        Returns:
            True if email is already in use
        """
        ...

    @abstractmethod
    async def count_by_school(self, school_id: SchoolId) -> int:
        """
        Count students in a school.

        Args:
            school_id: School to count students for

        Returns:
            Number of students in school
        """
        ...

    @abstractmethod
    async def delete(self, student_id: StudentId) -> None:
        """
        Delete a student by ID.

        Args:
            student_id: Unique student identifier

        Note:
            Does not commit - UnitOfWork handles transaction.
            Caller should verify student exists before calling.
        """
        ...
