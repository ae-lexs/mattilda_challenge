"""Domain entities."""

from mattilda_challenge.domain.entities.school import School
from mattilda_challenge.domain.entities.student import Student, StudentStatus

__all__ = [
    "School",
    "Student",
    "StudentStatus",
]
