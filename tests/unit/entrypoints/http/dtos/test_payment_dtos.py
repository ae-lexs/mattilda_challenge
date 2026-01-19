"""Tests for Payment DTOs validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from mattilda_challenge.entrypoints.http.dtos import PaymentCreateRequestDTO


class TestPaymentCreateRequestDTOValidation:
    """Tests for PaymentCreateRequestDTO validation."""

    def test_valid_create_request_succeeds(self) -> None:
        """Test that valid create request passes validation."""
        dto = PaymentCreateRequestDTO(
            invoice_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
            amount="500.00",
            payment_date="2024-01-15T10:30:00Z",
            payment_method="transfer",
            reference_number="REF-001",
        )
        assert dto.invoice_id == "7c9e6679-7425-40de-944b-e07fc1f90ae7"
        assert dto.amount == "500.00"
        assert dto.payment_method == "transfer"

    def test_valid_create_request_without_reference_number_succeeds(self) -> None:
        """Test that create request without reference number succeeds."""
        dto = PaymentCreateRequestDTO(
            invoice_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
            amount="500.00",
            payment_date="2024-01-15T10:30:00Z",
            payment_method="cash",
        )
        assert dto.reference_number is None

    def test_amount_with_invalid_format_fails_validation(self) -> None:
        """Test that amount without exactly 2 decimal places fails."""
        with pytest.raises(ValidationError) as exc_info:
            PaymentCreateRequestDTO(
                invoice_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
                amount="500",  # Missing decimal places
                payment_date="2024-01-15T10:30:00Z",
                payment_method="transfer",
            )
        assert "amount" in str(exc_info.value)

    def test_amount_with_three_decimal_places_fails_validation(self) -> None:
        """Test that amount with three decimal places fails."""
        with pytest.raises(ValidationError) as exc_info:
            PaymentCreateRequestDTO(
                invoice_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
                amount="500.000",
                payment_date="2024-01-15T10:30:00Z",
                payment_method="transfer",
            )
        assert "amount" in str(exc_info.value)

    def test_empty_payment_method_fails_validation(self) -> None:
        """Test that empty payment method fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            PaymentCreateRequestDTO(
                invoice_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
                amount="500.00",
                payment_date="2024-01-15T10:30:00Z",
                payment_method="",
            )
        assert "payment_method" in str(exc_info.value)

    def test_payment_method_exceeding_max_length_fails_validation(self) -> None:
        """Test that payment method exceeding 50 characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            PaymentCreateRequestDTO(
                invoice_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
                amount="500.00",
                payment_date="2024-01-15T10:30:00Z",
                payment_method="A" * 51,
            )
        assert "payment_method" in str(exc_info.value)

    def test_reference_number_exceeding_max_length_fails_validation(self) -> None:
        """Test that reference number exceeding 100 characters fails."""
        with pytest.raises(ValidationError) as exc_info:
            PaymentCreateRequestDTO(
                invoice_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
                amount="500.00",
                payment_date="2024-01-15T10:30:00Z",
                payment_method="transfer",
                reference_number="A" * 101,
            )
        assert "reference_number" in str(exc_info.value)

    def test_valid_amount_formats_succeed(self) -> None:
        """Test that various valid amount formats succeed."""
        valid_amounts = ["0.00", "100.00", "9999999.99", "0.01"]
        for amount in valid_amounts:
            dto = PaymentCreateRequestDTO(
                invoice_id="7c9e6679-7425-40de-944b-e07fc1f90ae7",
                amount=amount,
                payment_date="2024-01-15T10:30:00Z",
                payment_method="transfer",
            )
            assert dto.amount == amount
