"""Tests for SchoolMapper."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.infrastructure.postgres.mappers import SchoolMapper
from mattilda_challenge.infrastructure.postgres.models import SchoolModel


class TestSchoolMapperToEntity:
    """Tests for SchoolMapper.to_entity()."""

    def test_converts_model_to_entity(self) -> None:
        """Test that to_entity converts all fields correctly."""
        model_id = uuid4()
        created_at = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        model = SchoolModel(
            id=model_id,
            name="Test School",
            address="123 Test Street",
            created_at=created_at,
        )

        entity = SchoolMapper.to_entity(model)

        assert isinstance(entity, School)
        assert isinstance(entity.id, SchoolId)
        assert entity.id.value == model_id
        assert entity.name == "Test School"
        assert entity.address == "123 Test Street"
        assert entity.created_at == created_at

    def test_converts_uuid_to_school_id(self) -> None:
        """Test that raw UUID is wrapped in SchoolId value object."""
        model_id = uuid4()

        model = SchoolModel(
            id=model_id,
            name="Test School",
            address="123 Test Street",
            created_at=datetime.now(UTC),
        )

        entity = SchoolMapper.to_entity(model)

        assert entity.id.value == model_id
        assert str(entity.id) == str(model_id)


class TestSchoolMapperToModel:
    """Tests for SchoolMapper.to_model()."""

    def test_converts_entity_to_model(self) -> None:
        """Test that to_model converts all fields correctly."""
        school_id = SchoolId.generate()
        created_at = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        entity = School(
            id=school_id,
            name="Test School",
            address="123 Test Street",
            created_at=created_at,
        )

        model = SchoolMapper.to_model(entity)

        assert isinstance(model, SchoolModel)
        assert model.id == school_id.value
        assert model.name == "Test School"
        assert model.address == "123 Test Street"
        assert model.created_at == created_at

    def test_unwraps_school_id_to_uuid(self) -> None:
        """Test that SchoolId value object is unwrapped to raw UUID."""
        school_id = SchoolId.generate()

        entity = School(
            id=school_id,
            name="Test School",
            address="123 Test Street",
            created_at=datetime.now(UTC),
        )

        model = SchoolMapper.to_model(entity)

        assert model.id == school_id.value
        assert isinstance(model.id, type(school_id.value))


class TestSchoolMapperRoundTrip:
    """Tests for round-trip conversion."""

    def test_entity_to_model_to_entity_preserves_data(self) -> None:
        """Test that entity -> model -> entity produces equivalent result."""
        original = School.create(
            name="Round Trip School",
            address="456 Round Trip Ave",
            now=datetime(2024, 6, 15, 10, 30, 0, tzinfo=UTC),
        )

        model = SchoolMapper.to_model(original)
        restored = SchoolMapper.to_entity(model)

        assert restored == original
        assert restored.id == original.id
        assert restored.name == original.name
        assert restored.address == original.address
        assert restored.created_at == original.created_at

    def test_model_to_entity_to_model_preserves_data(self) -> None:
        """Test that model -> entity -> model produces equivalent data."""
        model_id = uuid4()
        created_at = datetime(2024, 3, 20, 14, 0, 0, tzinfo=UTC)

        original_model = SchoolModel(
            id=model_id,
            name="Model School",
            address="789 Model Blvd",
            created_at=created_at,
        )

        entity = SchoolMapper.to_entity(original_model)
        restored_model = SchoolMapper.to_model(entity)

        assert restored_model.id == original_model.id
        assert restored_model.name == original_model.name
        assert restored_model.address == original_model.address
        assert restored_model.created_at == original_model.created_at
