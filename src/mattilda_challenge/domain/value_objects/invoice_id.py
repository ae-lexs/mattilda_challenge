from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from mattilda_challenge.domain.exceptions import InvalidInvoiceIdError


@dataclass(frozen=True, slots=True)
class InvoiceId:
    """
    Invoice identifier value object.

    Encapsulates UUID validation and ensures type safety.
    Immutable and hashable.
    """

    value: UUID

    def __post_init__(self) -> None:
        """Validate UUID type at construction."""
        if not isinstance(self.value, UUID):
            raise InvalidInvoiceIdError(
                f"Expected UUID, got {type(self.value).__name__}"
            )

    @classmethod
    def generate(cls) -> InvoiceId:
        """Generate new unique invoice ID."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_str: str) -> InvoiceId:
        """
        Parse invoice ID from string representation.

        Args:
            id_str: UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")

        Returns:
            InvoiceId instance

        Raises:
            InvalidInvoiceIdError: If string is not a valid UUID
        """
        try:
            return cls(value=UUID(id_str))
        except (ValueError, AttributeError) as e:
            raise InvalidInvoiceIdError(f"Invalid UUID string: {id_str}") from e

    def __str__(self) -> str:
        """Return string representation for display/logging."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return detailed representation for debugging."""
        return f"InvoiceId({self.value!r})"
