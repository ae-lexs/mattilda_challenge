"""Tests for StudentMapper (HTTP layer)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId, StudentStatus
from mattilda_challenge.entrypoints.http.dtos import (
    StudentCreateRequestDTO,
    StudentUpdateRequestDTO,
)
from mattilda_challenge.entrypoints.http.mappers import StudentMapper


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_school_id() -> SchoolId:
    """Provide fixed school ID for testing."""
    return SchoolId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def sample_student(
    fixed_student_id: StudentId,
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> Student:
    """Provide sample student entity for testing."""
    return Student(
        id=fixed_student_id,
        school_id=fixed_school_id,
        first_name="John",
        last_name="Doe",
        email="john.doe@test.com",
        enrollment_date=fixed_time,
        status=StudentStatus.ACTIVE,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


class TestStudentMapperToCreateRequest:
    """Tests for StudentMapper.to_create_request()."""

    def test_converts_dto_to_create_request(self) -> None:
        """Test that to_create_request converts all fields correctly."""
        dto = StudentCreateRequestDTO(
            school_id="11111111-1111-1111-1111-111111111111",
            first_name="John",
            last_name="Doe",
            email="john.doe@test.com",
        )

        request = StudentMapper.to_create_request(dto)

        assert request.school_id.value == UUID("11111111-1111-1111-1111-111111111111")
        assert request.first_name == "John"
        assert request.last_name == "Doe"
        assert request.email == "john.doe@test.com"

    def test_strips_whitespace_from_first_name(self) -> None:
        """Test that whitespace is stripped from first name."""
        dto = StudentCreateRequestDTO(
            school_id="11111111-1111-1111-1111-111111111111",
            first_name="  John  ",
            last_name="Doe",
            email="john.doe@test.com",
        )

        request = StudentMapper.to_create_request(dto)

        assert request.first_name == "John"

    def test_strips_whitespace_from_last_name(self) -> None:
        """Test that whitespace is stripped from last name."""
        dto = StudentCreateRequestDTO(
            school_id="11111111-1111-1111-1111-111111111111",
            first_name="John",
            last_name="  Doe  ",
            email="john.doe@test.com",
        )

        request = StudentMapper.to_create_request(dto)

        assert request.last_name == "Doe"

    def test_normalizes_email_to_lowercase(self) -> None:
        """Test that email is converted to lowercase."""
        dto = StudentCreateRequestDTO(
            school_id="11111111-1111-1111-1111-111111111111",
            first_name="John",
            last_name="Doe",
            email="John.Doe@Test.Com",
        )

        request = StudentMapper.to_create_request(dto)

        assert request.email == "john.doe@test.com"

    def test_strips_whitespace_from_email(self) -> None:
        """Test that whitespace is stripped from email."""
        dto = StudentCreateRequestDTO(
            school_id="11111111-1111-1111-1111-111111111111",
            first_name="John",
            last_name="Doe",
            email="  john.doe@test.com  ",
        )

        request = StudentMapper.to_create_request(dto)

        assert request.email == "john.doe@test.com"


class TestStudentMapperToUpdateRequest:
    """Tests for StudentMapper.to_update_request()."""

    def test_converts_dto_with_all_fields(self) -> None:
        """Test that to_update_request converts all fields correctly."""
        student_id = "22222222-2222-2222-2222-222222222222"
        dto = StudentUpdateRequestDTO(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
            status="inactive",
        )

        request = StudentMapper.to_update_request(student_id, dto)

        assert request.student_id.value == UUID(student_id)
        assert request.first_name == "Jane"
        assert request.last_name == "Smith"
        assert request.email == "jane.smith@test.com"
        assert request.status == StudentStatus.INACTIVE

    def test_converts_dto_with_partial_fields(self) -> None:
        """Test that to_update_request handles partial updates."""
        student_id = "22222222-2222-2222-2222-222222222222"
        dto = StudentUpdateRequestDTO(first_name="Jane")

        request = StudentMapper.to_update_request(student_id, dto)

        assert request.first_name == "Jane"
        assert request.last_name is None
        assert request.email is None
        assert request.status is None

    def test_normalizes_status_to_enum(self) -> None:
        """Test that status string is converted to enum."""
        student_id = "22222222-2222-2222-2222-222222222222"
        dto = StudentUpdateRequestDTO(status="GRADUATED")

        request = StudentMapper.to_update_request(student_id, dto)

        assert request.status == StudentStatus.GRADUATED

    def test_normalizes_email_to_lowercase(self) -> None:
        """Test that email is converted to lowercase in update."""
        student_id = "22222222-2222-2222-2222-222222222222"
        dto = StudentUpdateRequestDTO(email="Jane.Smith@Test.Com")

        request = StudentMapper.to_update_request(student_id, dto)

        assert request.email == "jane.smith@test.com"


class TestStudentMapperToResponse:
    """Tests for StudentMapper.to_response()."""

    def test_converts_entity_to_response(
        self,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test that to_response converts all fields correctly."""
        response = StudentMapper.to_response(sample_student, fixed_time)

        assert response.id == str(sample_student.id.value)
        assert response.school_id == str(sample_student.school_id.value)
        assert response.first_name == sample_student.first_name
        assert response.last_name == sample_student.last_name
        assert response.email == sample_student.email
        assert response.status == sample_student.status.value

    def test_formats_dates_as_iso8601_utc(
        self,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test that dates are formatted as ISO 8601 with Z suffix."""
        response = StudentMapper.to_response(sample_student, fixed_time)

        assert response.enrollment_date == "2024-01-15T12:00:00Z"
        assert response.created_at == "2024-01-15T12:00:00Z"
        assert response.updated_at == "2024-01-15T12:00:00Z"
        assert all(
            date.endswith("Z")
            for date in [
                response.enrollment_date,
                response.created_at,
                response.updated_at,
            ]
        )

    def test_converts_ids_to_strings(
        self,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test that ID value objects are converted to strings."""
        response = StudentMapper.to_response(sample_student, fixed_time)

        assert isinstance(response.id, str)
        assert isinstance(response.school_id, str)
        assert response.id == "22222222-2222-2222-2222-222222222222"
        assert response.school_id == "11111111-1111-1111-1111-111111111111"
