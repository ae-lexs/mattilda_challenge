"""Invoice identifier value object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mattilda_challenge.domain.exceptions import InvalidIdError, InvalidInvoiceIdError
from mattilda_challenge.domain.value_objects.entity_id import EntityId


@dataclass(frozen=True, slots=True, repr=False)
class InvoiceId(EntityId):
    """
    Invoice identifier value object.

    Encapsulates UUID validation and ensures type safety.
    Immutable and hashable.
    """

    _exception_class: ClassVar[type[InvalidIdError]] = InvalidInvoiceIdError
