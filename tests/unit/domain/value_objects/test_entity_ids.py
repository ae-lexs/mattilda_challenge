"""Parametrized tests for all entity ID value objects."""

from __future__ import annotations

from uuid import UUID

import pytest

from mattilda_challenge.domain.exceptions import (
    InvalidIdError,
    InvalidInvoiceIdError,
    InvalidPaymentIdError,
    InvalidSchoolIdError,
    InvalidStudentIdError,
)
from mattilda_challenge.domain.value_objects import (
    EntityId,
    InvoiceId,
    PaymentId,
    SchoolId,
    StudentId,
)

VALID_UUID_STR = "550e8400-e29b-41d4-a716-446655440000"
VALID_UUID = UUID(VALID_UUID_STR)


@pytest.mark.parametrize(
    ("id_class", "exception_class"),
    [
        (SchoolId, InvalidSchoolIdError),
        (StudentId, InvalidStudentIdError),
        (InvoiceId, InvalidInvoiceIdError),
        (PaymentId, InvalidPaymentIdError),
    ],
)
class TestEntityIds:
    """Parametrized tests covering all entity ID types."""

    def test_create_with_valid_uuid(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test creating ID with valid UUID."""
        entity_id = id_class(value=VALID_UUID)

        assert entity_id.value == VALID_UUID

    def test_generate_creates_valid_id(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test generate() creates a valid UUID-based ID."""
        entity_id = id_class.generate()

        assert isinstance(entity_id.value, UUID)
        assert isinstance(entity_id, id_class)

    def test_generate_creates_unique_ids(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test generate() creates unique IDs on each call."""
        id1 = id_class.generate()
        id2 = id_class.generate()

        assert id1.value != id2.value

    def test_from_string_valid_uuid(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test from_string() parses valid UUID string."""
        entity_id = id_class.from_string(VALID_UUID_STR)

        assert entity_id.value == VALID_UUID
        assert str(entity_id) == VALID_UUID_STR

    def test_from_string_invalid_raises_exception(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],
    ) -> None:
        """Test from_string() raises correct exception for invalid string."""
        with pytest.raises(exception_class) as exc_info:
            id_class.from_string("not-a-valid-uuid")

        assert "Invalid UUID string" in str(exc_info.value)

    def test_from_string_empty_raises_exception(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],
    ) -> None:
        """Test from_string() raises correct exception for empty string."""
        with pytest.raises(exception_class):
            id_class.from_string("")

    def test_invalid_type_raises_exception(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],
    ) -> None:
        """Test constructor raises correct exception for non-UUID type."""
        with pytest.raises(exception_class) as exc_info:
            id_class(value="not-a-uuid")  # type: ignore[arg-type]

        assert "Expected UUID" in str(exc_info.value)

    def test_str_returns_uuid_string(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test __str__() returns UUID as string."""
        entity_id = id_class(value=VALID_UUID)

        assert str(entity_id) == VALID_UUID_STR

    def test_repr_includes_class_name(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test __repr__() includes class name and UUID."""
        entity_id = id_class(value=VALID_UUID)
        repr_str = repr(entity_id)

        assert id_class.__name__ in repr_str
        assert str(VALID_UUID) in repr_str

    def test_equality(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test two IDs with same UUID are equal."""
        id1 = id_class(value=VALID_UUID)
        id2 = id_class(value=VALID_UUID)

        assert id1 == id2

    def test_inequality(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test two IDs with different UUIDs are not equal."""
        id1 = id_class.generate()
        id2 = id_class.generate()

        assert id1 != id2

    def test_hashable(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test IDs are hashable and can be used in sets/dicts."""
        entity_id = id_class(value=VALID_UUID)

        # Should not raise
        hash_value = hash(entity_id)
        assert isinstance(hash_value, int)

        # Can be used in set
        id_set = {entity_id}
        assert entity_id in id_set

        # Can be used as dict key
        id_dict = {entity_id: "value"}
        assert id_dict[entity_id] == "value"

    def test_immutable(
        self,
        id_class: type[EntityId],
        exception_class: type[InvalidIdError],  # noqa: ARG002
    ) -> None:
        """Test IDs are immutable (frozen dataclass)."""
        entity_id = id_class(value=VALID_UUID)

        with pytest.raises(AttributeError):
            entity_id.value = UUID("00000000-0000-0000-0000-000000000000")  # type: ignore[misc]


class TestEntityIdTypeDistinction:
    """Test that different ID types are distinct."""

    def test_different_id_types_not_equal(self) -> None:
        """Test that IDs of different types are not equal even with same UUID."""
        school_id = SchoolId(value=VALID_UUID)
        student_id = StudentId(value=VALID_UUID)

        # Same UUID but different types
        assert school_id != student_id

    def test_isinstance_checks(self) -> None:
        """Test isinstance correctly distinguishes ID types."""
        school_id = SchoolId.generate()
        student_id = StudentId.generate()

        assert isinstance(school_id, SchoolId)
        assert isinstance(school_id, EntityId)
        assert not isinstance(school_id, StudentId)

        assert isinstance(student_id, StudentId)
        assert isinstance(student_id, EntityId)
        assert not isinstance(student_id, SchoolId)
