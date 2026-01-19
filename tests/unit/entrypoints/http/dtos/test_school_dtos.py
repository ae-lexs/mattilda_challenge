"""Tests for School DTOs validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mattilda_challenge.entrypoints.http.dtos import (
    SchoolCreateRequestDTO,
    SchoolUpdateRequestDTO,
)


class TestSchoolCreateRequestDTOValidation:
    """Tests for SchoolCreateRequestDTO validation."""

    def test_valid_create_request_succeeds(self) -> None:
        """Test that valid create request passes validation."""
        dto = SchoolCreateRequestDTO(
            name="Test School",
            address="123 Test Street",
        )
        assert dto.name == "Test School"
        assert dto.address == "123 Test Street"

    def test_empty_name_fails_validation(self) -> None:
        """Test that empty name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolCreateRequestDTO(
                name="",
                address="123 Test Street",
            )
        assert "name" in str(exc_info.value)

    def test_name_exceeding_max_length_fails_validation(self) -> None:
        """Test that name exceeding 255 characters fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolCreateRequestDTO(
                name="A" * 256,
                address="123 Test Street",
            )
        assert "name" in str(exc_info.value)

    def test_name_at_max_length_succeeds(self) -> None:
        """Test that name at exactly 255 characters succeeds."""
        dto = SchoolCreateRequestDTO(
            name="A" * 255,
            address="123 Test Street",
        )
        assert len(dto.name) == 255

    def test_empty_address_fails_validation(self) -> None:
        """Test that empty address fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolCreateRequestDTO(
                name="Test School",
                address="",
            )
        assert "address" in str(exc_info.value)

    def test_address_exceeding_max_length_fails_validation(self) -> None:
        """Test that address exceeding 500 characters fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolCreateRequestDTO(
                name="Test School",
                address="A" * 501,
            )
        assert "address" in str(exc_info.value)

    def test_address_at_max_length_succeeds(self) -> None:
        """Test that address at exactly 500 characters succeeds."""
        dto = SchoolCreateRequestDTO(
            name="Test School",
            address="A" * 500,
        )
        assert len(dto.address) == 500

    def test_missing_name_fails_validation(self) -> None:
        """Test that missing name field fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolCreateRequestDTO(address="123 Test Street")  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_missing_address_fails_validation(self) -> None:
        """Test that missing address field fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolCreateRequestDTO(name="Test School")  # type: ignore[call-arg]
        assert "address" in str(exc_info.value)


class TestSchoolUpdateRequestDTOValidation:
    """Tests for SchoolUpdateRequestDTO validation."""

    def test_valid_update_with_name_only_succeeds(self) -> None:
        """Test that update with only name succeeds."""
        dto = SchoolUpdateRequestDTO(name="Updated Name")
        assert dto.name == "Updated Name"
        assert dto.address is None

    def test_valid_update_with_address_only_succeeds(self) -> None:
        """Test that update with only address succeeds."""
        dto = SchoolUpdateRequestDTO(address="Updated Address")
        assert dto.name is None
        assert dto.address == "Updated Address"

    def test_valid_update_with_both_fields_succeeds(self) -> None:
        """Test that update with both fields succeeds."""
        dto = SchoolUpdateRequestDTO(
            name="Updated Name",
            address="Updated Address",
        )
        assert dto.name == "Updated Name"
        assert dto.address == "Updated Address"

    def test_empty_update_succeeds(self) -> None:
        """Test that empty update succeeds (no fields provided)."""
        dto = SchoolUpdateRequestDTO()
        assert dto.name is None
        assert dto.address is None

    def test_empty_name_string_fails_validation(self) -> None:
        """Test that empty string for name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolUpdateRequestDTO(name="")
        assert "name" in str(exc_info.value)

    def test_empty_address_string_fails_validation(self) -> None:
        """Test that empty string for address fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolUpdateRequestDTO(address="")
        assert "address" in str(exc_info.value)

    def test_name_exceeding_max_length_fails_validation(self) -> None:
        """Test that name exceeding 255 characters fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolUpdateRequestDTO(name="A" * 256)
        assert "name" in str(exc_info.value)

    def test_address_exceeding_max_length_fails_validation(self) -> None:
        """Test that address exceeding 500 characters fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            SchoolUpdateRequestDTO(address="A" * 501)
        assert "address" in str(exc_info.value)
