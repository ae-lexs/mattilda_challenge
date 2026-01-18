"""Student identifier value object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from mattilda_challenge.domain.exceptions import InvalidIdError, InvalidStudentIdError
from mattilda_challenge.domain.value_objects.entity_id import EntityId


@dataclass(frozen=True, slots=True, repr=False)
class StudentId(EntityId):
    """
    Student identifier value object.

    Encapsulates UUID validation and ensures type safety.
    Immutable and hashable.
    """

    _exception_class: ClassVar[type[InvalidIdError]] = InvalidStudentIdError
