"""Tests for SchoolMapper (HTTP layer)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.entrypoints.http.dtos import (
    SchoolCreateRequestDTO,
    SchoolUpdateRequestDTO,
)
from mattilda_challenge.entrypoints.http.mappers import SchoolMapper


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_school_id() -> SchoolId:
    """Provide fixed school ID for testing."""
    return SchoolId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def sample_school(fixed_school_id: SchoolId, fixed_time: datetime) -> School:
    """Provide sample school entity for testing."""
    return School(
        id=fixed_school_id,
        name="Test School",
        address="123 Test Street",
        created_at=fixed_time,
    )


class TestSchoolMapperToCreateRequest:
    """Tests for SchoolMapper.to_create_request()."""

    def test_converts_dto_to_create_request(self) -> None:
        """Test that to_create_request converts all fields correctly."""
        dto = SchoolCreateRequestDTO(
            name="Test School",
            address="123 Test Street",
        )

        request = SchoolMapper.to_create_request(dto)

        assert request.name == "Test School"
        assert request.address == "123 Test Street"

    def test_strips_whitespace_from_name(self) -> None:
        """Test that whitespace is stripped from name."""
        dto = SchoolCreateRequestDTO(
            name="  Test School  ",
            address="123 Test Street",
        )

        request = SchoolMapper.to_create_request(dto)

        assert request.name == "Test School"

    def test_strips_whitespace_from_address(self) -> None:
        """Test that whitespace is stripped from address."""
        dto = SchoolCreateRequestDTO(
            name="Test School",
            address="  123 Test Street  ",
        )

        request = SchoolMapper.to_create_request(dto)

        assert request.address == "123 Test Street"


class TestSchoolMapperToUpdateRequest:
    """Tests for SchoolMapper.to_update_request()."""

    def test_converts_dto_with_all_fields(self) -> None:
        """Test that to_update_request converts all fields correctly."""
        school_id = "11111111-1111-1111-1111-111111111111"
        dto = SchoolUpdateRequestDTO(
            name="Updated Name",
            address="Updated Address",
        )

        request = SchoolMapper.to_update_request(school_id, dto)

        assert request.school_id.value == UUID(school_id)
        assert request.name == "Updated Name"
        assert request.address == "Updated Address"

    def test_converts_dto_with_name_only(self) -> None:
        """Test that to_update_request handles name-only update."""
        school_id = "11111111-1111-1111-1111-111111111111"
        dto = SchoolUpdateRequestDTO(name="Updated Name")

        request = SchoolMapper.to_update_request(school_id, dto)

        assert request.name == "Updated Name"
        assert request.address is None

    def test_converts_dto_with_address_only(self) -> None:
        """Test that to_update_request handles address-only update."""
        school_id = "11111111-1111-1111-1111-111111111111"
        dto = SchoolUpdateRequestDTO(address="Updated Address")

        request = SchoolMapper.to_update_request(school_id, dto)

        assert request.name is None
        assert request.address == "Updated Address"

    def test_strips_whitespace_from_name(self) -> None:
        """Test that whitespace is stripped from name."""
        school_id = "11111111-1111-1111-1111-111111111111"
        dto = SchoolUpdateRequestDTO(name="  Updated Name  ")

        request = SchoolMapper.to_update_request(school_id, dto)

        assert request.name == "Updated Name"

    def test_strips_whitespace_from_address(self) -> None:
        """Test that whitespace is stripped from address."""
        school_id = "11111111-1111-1111-1111-111111111111"
        dto = SchoolUpdateRequestDTO(address="  Updated Address  ")

        request = SchoolMapper.to_update_request(school_id, dto)

        assert request.address == "Updated Address"


class TestSchoolMapperToResponse:
    """Tests for SchoolMapper.to_response()."""

    def test_converts_entity_to_response(
        self,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test that to_response converts all fields correctly."""
        response = SchoolMapper.to_response(sample_school, fixed_time)

        assert response.id == str(sample_school.id.value)
        assert response.name == sample_school.name
        assert response.address == sample_school.address

    def test_formats_created_at_as_iso8601_utc(
        self,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test that created_at is formatted as ISO 8601 with Z suffix."""
        response = SchoolMapper.to_response(sample_school, fixed_time)

        assert response.created_at == "2024-01-15T12:00:00Z"
        assert response.created_at.endswith("Z")

    def test_converts_school_id_to_string(
        self,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test that school ID value object is converted to string."""
        response = SchoolMapper.to_response(sample_school, fixed_time)

        assert response.id == "11111111-1111-1111-1111-111111111111"
        assert isinstance(response.id, str)


class TestSchoolMapperRoundTrip:
    """Tests for round-trip conversion."""

    def test_create_request_to_entity_to_response(self, fixed_time: datetime) -> None:
        """Test full flow: DTO -> domain request -> entity -> response DTO."""
        # Start with create DTO
        create_dto = SchoolCreateRequestDTO(
            name="Round Trip School",
            address="456 Round Trip Ave",
        )

        # Convert to domain request
        request = SchoolMapper.to_create_request(create_dto)

        # Create entity (simulating use case)
        entity = School.create(
            name=request.name,
            address=request.address,
            now=fixed_time,
        )

        # Convert to response DTO
        response = SchoolMapper.to_response(entity, fixed_time)

        # Verify data integrity
        assert response.name == create_dto.name
        assert response.address == create_dto.address
        assert response.created_at == "2024-01-15T12:00:00Z"
