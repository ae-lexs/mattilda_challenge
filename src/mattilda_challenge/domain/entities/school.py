from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from mattilda_challenge.domain.exceptions import InvalidSchoolDataError
from mattilda_challenge.domain.value_objects import SchoolId


@dataclass(frozen=True, slots=True)
class School:
    """
    School entity representing an educational institution.

    Immutable. Changes return new instances via copy-on-write.
    """

    id: SchoolId
    name: str
    address: str
    created_at: datetime

    def __post_init__(self) -> None:
        """Validate invariants at construction."""
        if not self.name or not self.name.strip():
            raise InvalidSchoolDataError("School name cannot be empty")

        if not self.address or not self.address.strip():
            raise InvalidSchoolDataError("School address cannot be empty")

        if self.created_at.tzinfo != UTC:
            raise InvalidSchoolDataError(
                f"Created timestamp must have UTC timezone, got {self.created_at.tzinfo}"
            )

    @classmethod
    def create(cls, name: str, address: str, now: datetime) -> School:
        """
        Create new school with generated ID.

        Args:
            name: School name
            address: School address
            now: Current timestamp (injected)

        Returns:
            New school instance
        """
        return cls(
            id=SchoolId.generate(),
            name=name.strip(),
            address=address.strip(),
            created_at=now,
        )
