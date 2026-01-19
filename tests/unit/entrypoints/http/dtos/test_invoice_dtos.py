"""Tests for Invoice DTOs validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mattilda_challenge.entrypoints.http.dtos import (
    CancelInvoiceRequestDTO,
    InvoiceCreateRequestDTO,
)


class TestInvoiceCreateRequestDTOValidation:
    """Tests for InvoiceCreateRequestDTO validation."""

    def test_valid_create_request_succeeds(self) -> None:
        """Test that valid create request passes validation."""
        dto = InvoiceCreateRequestDTO(
            student_id="550e8400-e29b-41d4-a716-446655440000",
            amount="1500.00",
            due_date="2024-02-15T00:00:00Z",
            description="January 2024 Tuition",
            late_fee_policy_monthly_rate="0.05",
        )
        assert dto.student_id == "550e8400-e29b-41d4-a716-446655440000"
        assert dto.amount == "1500.00"
        assert dto.late_fee_policy_monthly_rate == "0.05"

    def test_amount_with_invalid_format_fails_validation(self) -> None:
        """Test that amount without exactly 2 decimal places fails."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceCreateRequestDTO(
                student_id="550e8400-e29b-41d4-a716-446655440000",
                amount="1500",  # Missing decimal places
                due_date="2024-02-15T00:00:00Z",
                description="January 2024 Tuition",
                late_fee_policy_monthly_rate="0.05",
            )
        assert "amount" in str(exc_info.value)

    def test_amount_with_three_decimal_places_fails_validation(self) -> None:
        """Test that amount with three decimal places fails."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceCreateRequestDTO(
                student_id="550e8400-e29b-41d4-a716-446655440000",
                amount="1500.000",  # Three decimal places
                due_date="2024-02-15T00:00:00Z",
                description="January 2024 Tuition",
                late_fee_policy_monthly_rate="0.05",
            )
        assert "amount" in str(exc_info.value)

    def test_amount_with_one_decimal_place_fails_validation(self) -> None:
        """Test that amount with one decimal place fails."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceCreateRequestDTO(
                student_id="550e8400-e29b-41d4-a716-446655440000",
                amount="1500.0",  # One decimal place
                due_date="2024-02-15T00:00:00Z",
                description="January 2024 Tuition",
                late_fee_policy_monthly_rate="0.05",
            )
        assert "amount" in str(exc_info.value)

    def test_late_fee_rate_with_invalid_format_fails_validation(self) -> None:
        """Test that late fee rate without leading zero fails."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceCreateRequestDTO(
                student_id="550e8400-e29b-41d4-a716-446655440000",
                amount="1500.00",
                due_date="2024-02-15T00:00:00Z",
                description="January 2024 Tuition",
                late_fee_policy_monthly_rate="5",  # Invalid format
            )
        assert "late_fee_policy_monthly_rate" in str(exc_info.value)

    def test_late_fee_rate_with_two_decimals_succeeds(self) -> None:
        """Test that late fee rate with 2 decimal places succeeds."""
        dto = InvoiceCreateRequestDTO(
            student_id="550e8400-e29b-41d4-a716-446655440000",
            amount="1500.00",
            due_date="2024-02-15T00:00:00Z",
            description="January 2024 Tuition",
            late_fee_policy_monthly_rate="0.05",
        )
        assert dto.late_fee_policy_monthly_rate == "0.05"

    def test_late_fee_rate_with_four_decimals_succeeds(self) -> None:
        """Test that late fee rate with 4 decimal places succeeds."""
        dto = InvoiceCreateRequestDTO(
            student_id="550e8400-e29b-41d4-a716-446655440000",
            amount="1500.00",
            due_date="2024-02-15T00:00:00Z",
            description="January 2024 Tuition",
            late_fee_policy_monthly_rate="0.0525",
        )
        assert dto.late_fee_policy_monthly_rate == "0.0525"

    def test_late_fee_rate_zero_succeeds(self) -> None:
        """Test that zero late fee rate succeeds."""
        dto = InvoiceCreateRequestDTO(
            student_id="550e8400-e29b-41d4-a716-446655440000",
            amount="1500.00",
            due_date="2024-02-15T00:00:00Z",
            description="January 2024 Tuition",
            late_fee_policy_monthly_rate="0.00",
        )
        assert dto.late_fee_policy_monthly_rate == "0.00"

    def test_empty_description_fails_validation(self) -> None:
        """Test that empty description fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceCreateRequestDTO(
                student_id="550e8400-e29b-41d4-a716-446655440000",
                amount="1500.00",
                due_date="2024-02-15T00:00:00Z",
                description="",
                late_fee_policy_monthly_rate="0.05",
            )
        assert "description" in str(exc_info.value)

    def test_description_exceeding_max_length_fails_validation(self) -> None:
        """Test that description exceeding 500 characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            InvoiceCreateRequestDTO(
                student_id="550e8400-e29b-41d4-a716-446655440000",
                amount="1500.00",
                due_date="2024-02-15T00:00:00Z",
                description="A" * 501,
                late_fee_policy_monthly_rate="0.05",
            )
        assert "description" in str(exc_info.value)


class TestCancelInvoiceRequestDTOValidation:
    """Tests for CancelInvoiceRequestDTO validation."""

    def test_valid_cancel_request_succeeds(self) -> None:
        """Test that valid cancel request passes validation."""
        dto = CancelInvoiceRequestDTO(
            cancellation_reason="Student withdrew from school",
        )
        assert dto.cancellation_reason == "Student withdrew from school"

    def test_empty_cancellation_reason_fails_validation(self) -> None:
        """Test that empty cancellation reason fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            CancelInvoiceRequestDTO(cancellation_reason="")
        assert "cancellation_reason" in str(exc_info.value)

    def test_cancellation_reason_exceeding_max_length_fails_validation(self) -> None:
        """Test that cancellation reason exceeding 500 characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            CancelInvoiceRequestDTO(cancellation_reason="A" * 501)
        assert "cancellation_reason" in str(exc_info.value)

    def test_cancellation_reason_at_max_length_succeeds(self) -> None:
        """Test that cancellation reason at exactly 500 characters succeeds."""
        dto = CancelInvoiceRequestDTO(cancellation_reason="A" * 500)
        assert len(dto.cancellation_reason) == 500
