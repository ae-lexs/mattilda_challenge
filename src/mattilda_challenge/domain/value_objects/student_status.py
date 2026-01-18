from enum import Enum


class StudentStatus(str, Enum):
    """
    Student enrollment status.

    Inherits from str for JSON serialization.
    """

    ACTIVE = "active"  # Currently enrolled and attending
    INACTIVE = "inactive"  # Not currently attending (temporary)
    GRADUATED = "graduated"  # Completed studies

    def __str__(self) -> str:
        """Return string value for display."""
        return self.value
