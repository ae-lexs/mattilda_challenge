"""Base class for all entity identifiers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Self
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from mattilda_challenge.domain.exceptions import InvalidIdError


@dataclass(frozen=True)
class EntityId:
    """
    Base class for all entity identifiers.

    Provides UUID validation, generation, and parsing.
    Subclasses must define _exception_class to specify
    which exception to raise on validation failure.

    Note: Does not use slots=True to allow inheritance.
    Subclasses use slots=True for memory efficiency.
    """

    value: UUID
    _exception_class: ClassVar[type[InvalidIdError]]

    def __post_init__(self) -> None:
        """Validate UUID type at construction."""
        if not isinstance(self.value, UUID):
            raise self._exception_class(
                f"Expected UUID, got {type(self.value).__name__}"
            )

    @classmethod
    def generate(cls) -> Self:
        """Generate new unique ID."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> Self:
        """
        Parse ID from string representation.

        Args:
            id_str: UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")

        Returns:
            New instance of the ID class

        Raises:
            InvalidIdError subclass: If string is not a valid UUID
        """
        try:
            return cls(value=UUID(id_str))
        except (ValueError, AttributeError) as e:
            raise cls._exception_class(f"Invalid UUID string: {id_str}") from e

    def __str__(self) -> str:
        """Return string representation for display/logging."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return f"{self.__class__.__name__}({self.value!r})"
