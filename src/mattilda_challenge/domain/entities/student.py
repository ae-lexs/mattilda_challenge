from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime

from mattilda_challenge.domain.exceptions import InvalidStudentDataError
from mattilda_challenge.domain.value_objects import SchoolId, StudentId, StudentStatus


@dataclass(frozen=True, slots=True)
class Student:
    """
    Student entity representing an individual enrolled in a school.

    Relationship with school is immutable (1:1).
    Immutable. Changes return new instances via copy-on-write.
    """

    id: StudentId
    school_id: SchoolId  # Immutable - never changes after enrollment
    first_name: str
    last_name: str
    email: str
    enrollment_date: datetime
    status: StudentStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        """Validate invariants at construction."""
        if not self.first_name or not self.first_name.strip():
            raise InvalidStudentDataError("First name cannot be empty")

        if not self.last_name or not self.last_name.strip():
            raise InvalidStudentDataError("Last name cannot be empty")

        # Basic email validation (not RFC-compliant, but catches obvious errors)
        if (
            not self.email
            or "@" not in self.email
            or "." not in self.email.split("@")[-1]
        ):
            raise InvalidStudentDataError(f"Invalid email format: {self.email}")

        if self.enrollment_date.tzinfo != UTC:
            raise InvalidStudentDataError(
                f"Enrollment date must have UTC timezone, got {self.enrollment_date.tzinfo}"
            )

        if self.created_at.tzinfo != UTC:
            raise InvalidStudentDataError(
                f"Created timestamp must have UTC timezone, got {self.created_at.tzinfo}"
            )

        if self.updated_at.tzinfo != UTC:
            raise InvalidStudentDataError(
                f"Updated timestamp must have UTC timezone, got {self.updated_at.tzinfo}"
            )

    @classmethod
    def create(
        cls,
        school_id: SchoolId,
        first_name: str,
        last_name: str,
        email: str,
        now: datetime,
    ) -> Student:
        """
        Create new student enrolled in a school.

        Args:
            school_id: School where student is enrolled
            first_name: Student's first name
            last_name: Student's last name
            email: Student's email address
            now: Current timestamp (injected)

        Returns:
            New student instance with ACTIVE status
        """
        return cls(
            id=StudentId.generate(),
            school_id=school_id,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            email=email.strip().lower(),
            enrollment_date=now,
            status=StudentStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def deactivate(self, now: datetime) -> Student:
        """
        Return new student with status INACTIVE.

        Args:
            now: Current timestamp (injected)

        Returns:
            New student instance with INACTIVE status
        """
        return replace(self, status=StudentStatus.INACTIVE, updated_at=now)

    def graduate(self, now: datetime) -> Student:
        """
        Return new student with status GRADUATED.

        Args:
            now: Current timestamp (injected)

        Returns:
            New student instance with GRADUATED status
        """
        return replace(self, status=StudentStatus.GRADUATED, updated_at=now)

    @property
    def full_name(self) -> str:
        """Return student's full name."""
        return f"{self.first_name} {self.last_name}"
