"""Tests for Student DTOs validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mattilda_challenge.entrypoints.http.dtos import (
    StudentCreateRequestDTO,
    StudentUpdateRequestDTO,
)


class TestStudentCreateRequestDTOValidation:
    """Tests for StudentCreateRequestDTO validation."""

    def test_valid_create_request_succeeds(self) -> None:
        """Test that valid create request passes validation."""
        dto = StudentCreateRequestDTO(
            school_id="450e8400-e29b-41d4-a716-446655440000",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
        )
        assert dto.first_name == "John"
        assert dto.last_name == "Doe"
        assert dto.email == "john.doe@example.com"

    def test_empty_first_name_fails_validation(self) -> None:
        """Test that empty first name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            StudentCreateRequestDTO(
                school_id="450e8400-e29b-41d4-a716-446655440000",
                first_name="",
                last_name="Doe",
                email="john.doe@example.com",
            )
        assert "first_name" in str(exc_info.value)

    def test_empty_last_name_fails_validation(self) -> None:
        """Test that empty last name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            StudentCreateRequestDTO(
                school_id="450e8400-e29b-41d4-a716-446655440000",
                first_name="John",
                last_name="",
                email="john.doe@example.com",
            )
        assert "last_name" in str(exc_info.value)

    def test_first_name_exceeding_max_length_fails_validation(self) -> None:
        """Test that first name exceeding 100 characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            StudentCreateRequestDTO(
                school_id="450e8400-e29b-41d4-a716-446655440000",
                first_name="A" * 101,
                last_name="Doe",
                email="john.doe@example.com",
            )
        assert "first_name" in str(exc_info.value)

    def test_last_name_exceeding_max_length_fails_validation(self) -> None:
        """Test that last name exceeding 100 characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            StudentCreateRequestDTO(
                school_id="450e8400-e29b-41d4-a716-446655440000",
                first_name="John",
                last_name="A" * 101,
                email="john.doe@example.com",
            )
        assert "last_name" in str(exc_info.value)

    def test_invalid_email_format_fails_validation(self) -> None:
        """Test that invalid email format fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            StudentCreateRequestDTO(
                school_id="450e8400-e29b-41d4-a716-446655440000",
                first_name="John",
                last_name="Doe",
                email="not-an-email",
            )
        assert "email" in str(exc_info.value)

    def test_email_without_domain_fails_validation(self) -> None:
        """Test that email without domain fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            StudentCreateRequestDTO(
                school_id="450e8400-e29b-41d4-a716-446655440000",
                first_name="John",
                last_name="Doe",
                email="john@",
            )
        assert "email" in str(exc_info.value)

    def test_valid_email_formats_succeed(self) -> None:
        """Test that various valid email formats succeed."""
        valid_emails = [
            "john@example.com",
            "john.doe@example.com",
            "john+tag@example.com",
            "john@subdomain.example.com",
        ]
        for email in valid_emails:
            dto = StudentCreateRequestDTO(
                school_id="450e8400-e29b-41d4-a716-446655440000",
                first_name="John",
                last_name="Doe",
                email=email,
            )
            assert dto.email == email


class TestStudentUpdateRequestDTOValidation:
    """Tests for StudentUpdateRequestDTO validation."""

    def test_valid_update_with_first_name_only_succeeds(self) -> None:
        """Test that update with only first name succeeds."""
        dto = StudentUpdateRequestDTO(first_name="Jane")
        assert dto.first_name == "Jane"
        assert dto.last_name is None
        assert dto.email is None
        assert dto.status is None

    def test_valid_update_with_status_only_succeeds(self) -> None:
        """Test that update with only status succeeds."""
        dto = StudentUpdateRequestDTO(status="inactive")
        assert dto.status == "inactive"
        assert dto.first_name is None

    def test_empty_update_succeeds(self) -> None:
        """Test that empty update succeeds (no fields provided)."""
        dto = StudentUpdateRequestDTO()
        assert dto.first_name is None
        assert dto.last_name is None
        assert dto.email is None
        assert dto.status is None

    def test_empty_first_name_string_fails_validation(self) -> None:
        """Test that empty string for first name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            StudentUpdateRequestDTO(first_name="")
        assert "first_name" in str(exc_info.value)

    def test_empty_last_name_string_fails_validation(self) -> None:
        """Test that empty string for last name fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            StudentUpdateRequestDTO(last_name="")
        assert "last_name" in str(exc_info.value)

    def test_invalid_email_in_update_fails_validation(self) -> None:
        """Test that invalid email in update fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            StudentUpdateRequestDTO(email="not-an-email")
        assert "email" in str(exc_info.value)

    def test_valid_status_values_succeed(self) -> None:
        """Test that valid status values succeed."""
        valid_statuses = ["active", "inactive", "graduated", "suspended"]
        for status in valid_statuses:
            dto = StudentUpdateRequestDTO(status=status)
            assert dto.status == status
