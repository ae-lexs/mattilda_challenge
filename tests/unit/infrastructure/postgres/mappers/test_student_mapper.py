"""Tests for StudentMapper."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId, StudentStatus
from mattilda_challenge.infrastructure.postgres.mappers import StudentMapper
from mattilda_challenge.infrastructure.postgres.models import StudentModel


class TestStudentMapperToEntity:
    """Tests for StudentMapper.to_entity()."""

    def test_converts_model_to_entity(self) -> None:
        """Test that to_entity converts all fields correctly."""
        model_id = uuid4()
        school_id = uuid4()
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        model = StudentModel(
            id=model_id,
            school_id=school_id,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            enrollment_date=now,
            status="active",
            created_at=now,
            updated_at=now,
        )

        entity = StudentMapper.to_entity(model)

        assert isinstance(entity, Student)
        assert isinstance(entity.id, StudentId)
        assert isinstance(entity.school_id, SchoolId)
        assert entity.id.value == model_id
        assert entity.school_id.value == school_id
        assert entity.first_name == "John"
        assert entity.last_name == "Doe"
        assert entity.email == "john.doe@example.com"
        assert entity.enrollment_date == now
        assert entity.status == StudentStatus.ACTIVE
        assert entity.created_at == now
        assert entity.updated_at == now

    def test_converts_status_string_to_enum(self) -> None:
        """Test that status string is converted to StudentStatus enum."""
        now = datetime.now(UTC)

        for status_str, expected_enum in [
            ("active", StudentStatus.ACTIVE),
            ("inactive", StudentStatus.INACTIVE),
            ("graduated", StudentStatus.GRADUATED),
        ]:
            model = StudentModel(
                id=uuid4(),
                school_id=uuid4(),
                first_name="Test",
                last_name="User",
                email=f"test.{status_str}@example.com",
                enrollment_date=now,
                status=status_str,
                created_at=now,
                updated_at=now,
            )

            entity = StudentMapper.to_entity(model)

            assert entity.status == expected_enum


class TestStudentMapperToModel:
    """Tests for StudentMapper.to_model()."""

    def test_converts_entity_to_model(self) -> None:
        """Test that to_model converts all fields correctly."""
        student_id = StudentId.generate()
        school_id = SchoolId.generate()
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        entity = Student(
            id=student_id,
            school_id=school_id,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            enrollment_date=now,
            status=StudentStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        model = StudentMapper.to_model(entity)

        assert isinstance(model, StudentModel)
        assert model.id == student_id.value
        assert model.school_id == school_id.value
        assert model.first_name == "Jane"
        assert model.last_name == "Smith"
        assert model.email == "jane.smith@example.com"
        assert model.enrollment_date == now
        assert model.status == "active"
        assert model.created_at == now
        assert model.updated_at == now

    def test_converts_status_enum_to_string(self) -> None:
        """Test that StudentStatus enum is converted to string."""
        now = datetime.now(UTC)

        for status_enum, expected_str in [
            (StudentStatus.ACTIVE, "active"),
            (StudentStatus.INACTIVE, "inactive"),
            (StudentStatus.GRADUATED, "graduated"),
        ]:
            entity = Student(
                id=StudentId.generate(),
                school_id=SchoolId.generate(),
                first_name="Test",
                last_name="User",
                email=f"test.{expected_str}@example.com",
                enrollment_date=now,
                status=status_enum,
                created_at=now,
                updated_at=now,
            )

            model = StudentMapper.to_model(entity)

            assert model.status == expected_str


class TestStudentMapperRoundTrip:
    """Tests for round-trip conversion."""

    def test_entity_to_model_to_entity_preserves_data(self) -> None:
        """Test that entity -> model -> entity produces equivalent result."""
        school_id = SchoolId.generate()
        now = datetime(2024, 6, 15, 10, 30, 0, tzinfo=UTC)

        original = Student.create(
            school_id=school_id,
            first_name="Round",
            last_name="Trip",
            email="round.trip@example.com",
            now=now,
        )

        model = StudentMapper.to_model(original)
        restored = StudentMapper.to_entity(model)

        assert restored == original

    def test_model_to_entity_to_model_preserves_data(self) -> None:
        """Test that model -> entity -> model produces equivalent data."""
        model_id = uuid4()
        school_id = uuid4()
        now = datetime(2024, 3, 20, 14, 0, 0, tzinfo=UTC)

        original_model = StudentModel(
            id=model_id,
            school_id=school_id,
            first_name="Model",
            last_name="Student",
            email="model.student@example.com",
            enrollment_date=now,
            status="inactive",
            created_at=now,
            updated_at=now,
        )

        entity = StudentMapper.to_entity(original_model)
        restored_model = StudentMapper.to_model(entity)

        assert restored_model.id == original_model.id
        assert restored_model.school_id == original_model.school_id
        assert restored_model.first_name == original_model.first_name
        assert restored_model.last_name == original_model.last_name
        assert restored_model.email == original_model.email
        assert restored_model.enrollment_date == original_model.enrollment_date
        assert restored_model.status == original_model.status
        assert restored_model.created_at == original_model.created_at
        assert restored_model.updated_at == original_model.updated_at
