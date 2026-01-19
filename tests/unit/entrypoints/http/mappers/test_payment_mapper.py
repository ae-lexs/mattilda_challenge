"""Tests for PaymentMapper (HTTP layer)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId
from mattilda_challenge.entrypoints.http.dtos import PaymentCreateRequestDTO
from mattilda_challenge.entrypoints.http.mappers import PaymentMapper


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_payment_id() -> PaymentId:
    """Provide fixed payment ID for testing."""
    return PaymentId(value=UUID("44444444-4444-4444-4444-444444444444"))


@pytest.fixture
def fixed_invoice_id() -> InvoiceId:
    """Provide fixed invoice ID for testing."""
    return InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333"))


@pytest.fixture
def sample_payment(
    fixed_payment_id: PaymentId,
    fixed_invoice_id: InvoiceId,
    fixed_time: datetime,
) -> Payment:
    """Provide sample payment entity for testing."""
    return Payment(
        id=fixed_payment_id,
        invoice_id=fixed_invoice_id,
        amount=Decimal("500.00"),
        payment_date=fixed_time,
        payment_method="transfer",
        reference_number="REF-001",
        created_at=fixed_time,
    )


class TestPaymentMapperToCreateRequest:
    """Tests for PaymentMapper.to_create_request()."""

    def test_converts_dto_to_create_request(self, fixed_time: datetime) -> None:
        """Test that to_create_request converts all fields correctly."""
        dto = PaymentCreateRequestDTO(
            invoice_id="33333333-3333-3333-3333-333333333333",
            amount="500.00",
            payment_date="2024-01-15T10:30:00Z",
            payment_method="transfer",
            reference_number="REF-001",
        )

        request = PaymentMapper.to_create_request(dto, fixed_time)

        assert request.invoice_id.value == UUID("33333333-3333-3333-3333-333333333333")
        assert request.amount == Decimal("500.00")
        assert request.payment_date == datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        assert request.payment_method == "transfer"
        assert request.reference_number == "REF-001"

    def test_converts_amount_string_to_decimal(self, fixed_time: datetime) -> None:
        """Test that amount string is converted to Decimal."""
        dto = PaymentCreateRequestDTO(
            invoice_id="33333333-3333-3333-3333-333333333333",
            amount="750.50",
            payment_date="2024-01-15T10:30:00Z",
            payment_method="transfer",
        )

        request = PaymentMapper.to_create_request(dto, fixed_time)

        assert isinstance(request.amount, Decimal)
        assert request.amount == Decimal("750.50")

    def test_handles_null_reference_number(self, fixed_time: datetime) -> None:
        """Test that null reference number is handled correctly."""
        dto = PaymentCreateRequestDTO(
            invoice_id="33333333-3333-3333-3333-333333333333",
            amount="500.00",
            payment_date="2024-01-15T10:30:00Z",
            payment_method="cash",
        )

        request = PaymentMapper.to_create_request(dto, fixed_time)

        assert request.reference_number is None

    def test_strips_whitespace_from_payment_method(self, fixed_time: datetime) -> None:
        """Test that whitespace is stripped from payment method."""
        dto = PaymentCreateRequestDTO(
            invoice_id="33333333-3333-3333-3333-333333333333",
            amount="500.00",
            payment_date="2024-01-15T10:30:00Z",
            payment_method="  transfer  ",
        )

        request = PaymentMapper.to_create_request(dto, fixed_time)

        assert request.payment_method == "transfer"

    def test_strips_whitespace_from_reference_number(
        self, fixed_time: datetime
    ) -> None:
        """Test that whitespace is stripped from reference number."""
        dto = PaymentCreateRequestDTO(
            invoice_id="33333333-3333-3333-3333-333333333333",
            amount="500.00",
            payment_date="2024-01-15T10:30:00Z",
            payment_method="transfer",
            reference_number="  REF-001  ",
        )

        request = PaymentMapper.to_create_request(dto, fixed_time)

        assert request.reference_number == "REF-001"


class TestPaymentMapperToResponse:
    """Tests for PaymentMapper.to_response()."""

    def test_converts_entity_to_response(
        self,
        sample_payment: Payment,
    ) -> None:
        """Test that to_response converts all fields correctly."""
        response = PaymentMapper.to_response(sample_payment)

        assert response.id == str(sample_payment.id.value)
        assert response.invoice_id == str(sample_payment.invoice_id.value)
        assert response.amount == str(sample_payment.amount)
        assert response.payment_method == sample_payment.payment_method
        assert response.reference_number == sample_payment.reference_number

    def test_converts_decimal_to_string(
        self,
        sample_payment: Payment,
    ) -> None:
        """Test that Decimal values are converted to strings."""
        response = PaymentMapper.to_response(sample_payment)

        assert isinstance(response.amount, str)
        assert response.amount == "500.00"

    def test_formats_dates_as_iso8601_utc(
        self,
        sample_payment: Payment,
    ) -> None:
        """Test that dates are formatted as ISO 8601 with Z suffix."""
        response = PaymentMapper.to_response(sample_payment)

        assert response.payment_date == "2024-01-15T12:00:00Z"
        assert response.created_at == "2024-01-15T12:00:00Z"
        assert response.payment_date.endswith("Z")
        assert response.created_at.endswith("Z")

    def test_converts_ids_to_strings(
        self,
        sample_payment: Payment,
    ) -> None:
        """Test that ID value objects are converted to strings."""
        response = PaymentMapper.to_response(sample_payment)

        assert isinstance(response.id, str)
        assert isinstance(response.invoice_id, str)
        assert response.id == "44444444-4444-4444-4444-444444444444"
        assert response.invoice_id == "33333333-3333-3333-3333-333333333333"

    def test_handles_null_reference_number(
        self,
        fixed_payment_id: PaymentId,
        fixed_invoice_id: InvoiceId,
        fixed_time: datetime,
    ) -> None:
        """Test that null reference number is preserved."""
        payment = Payment(
            id=fixed_payment_id,
            invoice_id=fixed_invoice_id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="cash",
            reference_number=None,
            created_at=fixed_time,
        )

        response = PaymentMapper.to_response(payment)

        assert response.reference_number is None
