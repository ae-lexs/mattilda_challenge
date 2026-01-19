"""Tests for InvoiceMapper (HTTP layer)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    StudentId,
)
from mattilda_challenge.entrypoints.http.dtos import (
    CancelInvoiceRequestDTO,
    InvoiceCreateRequestDTO,
)
from mattilda_challenge.entrypoints.http.mappers import InvoiceMapper
from mattilda_challenge.entrypoints.http.mappers.invoice_mapper import parse_iso8601_utc


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_invoice_id() -> InvoiceId:
    """Provide fixed invoice ID for testing."""
    return InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333"))


@pytest.fixture
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def standard_late_fee_policy() -> LateFeePolicy:
    """Provide standard late fee policy for testing."""
    return LateFeePolicy(monthly_rate=Decimal("0.05"))


@pytest.fixture
def sample_invoice(
    fixed_invoice_id: InvoiceId,
    fixed_student_id: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Provide sample invoice entity for testing."""
    due_date = datetime(2024, 2, 15, 0, 0, 0, tzinfo=UTC)
    return Invoice(
        id=fixed_invoice_id,
        student_id=fixed_student_id,
        invoice_number="INV-2024-000001",
        amount=Decimal("1500.00"),
        due_date=due_date,
        description="January 2024 Tuition",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PENDING,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


class TestParseIso8601Utc:
    """Tests for parse_iso8601_utc helper function."""

    def test_parses_z_suffix(self) -> None:
        """Test that Z suffix is parsed correctly."""
        result = parse_iso8601_utc("2024-01-15T10:30:00Z")
        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

    def test_parses_plus_zero_offset(self) -> None:
        """Test that +00:00 offset is parsed correctly."""
        result = parse_iso8601_utc("2024-01-15T10:30:00+00:00")
        assert result == datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

    def test_adds_utc_to_naive_datetime(self) -> None:
        """Test that UTC is added to naive datetime."""
        result = parse_iso8601_utc("2024-01-15T10:30:00")
        assert result.tzinfo == UTC

    def test_parses_datetime_with_microseconds(self) -> None:
        """Test that microseconds are preserved."""
        result = parse_iso8601_utc("2024-01-15T10:30:00.123456Z")
        assert result.microsecond == 123456


class TestInvoiceMapperToCreateRequest:
    """Tests for InvoiceMapper.to_create_request()."""

    def test_converts_dto_to_create_request(self, fixed_time: datetime) -> None:
        """Test that to_create_request converts all fields correctly."""
        dto = InvoiceCreateRequestDTO(
            student_id="22222222-2222-2222-2222-222222222222",
            amount="1500.00",
            due_date="2024-02-15T00:00:00Z",
            description="January 2024 Tuition",
            late_fee_policy_monthly_rate="0.05",
        )

        request = InvoiceMapper.to_create_request(dto, fixed_time)

        assert request.student_id.value == UUID("22222222-2222-2222-2222-222222222222")
        assert request.amount == Decimal("1500.00")
        assert request.due_date == datetime(2024, 2, 15, 0, 0, 0, tzinfo=UTC)
        assert request.description == "January 2024 Tuition"
        assert request.late_fee_policy.monthly_rate == Decimal("0.05")

    def test_converts_amount_string_to_decimal(self, fixed_time: datetime) -> None:
        """Test that amount string is converted to Decimal."""
        dto = InvoiceCreateRequestDTO(
            student_id="22222222-2222-2222-2222-222222222222",
            amount="2350.50",
            due_date="2024-02-15T00:00:00Z",
            description="Test",
            late_fee_policy_monthly_rate="0.05",
        )

        request = InvoiceMapper.to_create_request(dto, fixed_time)

        assert isinstance(request.amount, Decimal)
        assert request.amount == Decimal("2350.50")

    def test_converts_late_fee_rate_to_decimal(self, fixed_time: datetime) -> None:
        """Test that late fee rate string is converted to Decimal."""
        dto = InvoiceCreateRequestDTO(
            student_id="22222222-2222-2222-2222-222222222222",
            amount="1500.00",
            due_date="2024-02-15T00:00:00Z",
            description="Test",
            late_fee_policy_monthly_rate="0.0375",
        )

        request = InvoiceMapper.to_create_request(dto, fixed_time)

        assert isinstance(request.late_fee_policy.monthly_rate, Decimal)
        assert request.late_fee_policy.monthly_rate == Decimal("0.0375")

    def test_strips_whitespace_from_description(self, fixed_time: datetime) -> None:
        """Test that whitespace is stripped from description."""
        dto = InvoiceCreateRequestDTO(
            student_id="22222222-2222-2222-2222-222222222222",
            amount="1500.00",
            due_date="2024-02-15T00:00:00Z",
            description="  January 2024 Tuition  ",
            late_fee_policy_monthly_rate="0.05",
        )

        request = InvoiceMapper.to_create_request(dto, fixed_time)

        assert request.description == "January 2024 Tuition"


class TestInvoiceMapperToCancelRequest:
    """Tests for InvoiceMapper.to_cancel_request()."""

    def test_converts_dto_to_cancel_request(self) -> None:
        """Test that to_cancel_request converts all fields correctly."""
        invoice_id = "33333333-3333-3333-3333-333333333333"
        dto = CancelInvoiceRequestDTO(
            cancellation_reason="Student withdrew from school",
        )

        request = InvoiceMapper.to_cancel_request(invoice_id, dto)

        assert request.invoice_id.value == UUID(invoice_id)
        assert request.cancellation_reason == "Student withdrew from school"

    def test_strips_whitespace_from_cancellation_reason(self) -> None:
        """Test that whitespace is stripped from cancellation reason."""
        invoice_id = "33333333-3333-3333-3333-333333333333"
        dto = CancelInvoiceRequestDTO(
            cancellation_reason="  Student withdrew from school  ",
        )

        request = InvoiceMapper.to_cancel_request(invoice_id, dto)

        assert request.cancellation_reason == "Student withdrew from school"


class TestInvoiceMapperToResponse:
    """Tests for InvoiceMapper.to_response()."""

    def test_converts_entity_to_response(
        self,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test that to_response converts all fields correctly."""
        response = InvoiceMapper.to_response(sample_invoice, fixed_time)

        assert response.id == str(sample_invoice.id.value)
        assert response.student_id == str(sample_invoice.student_id.value)
        assert response.invoice_number == sample_invoice.invoice_number
        assert response.amount == str(sample_invoice.amount)
        assert response.description == sample_invoice.description
        assert response.status == sample_invoice.status.value

    def test_converts_decimal_to_string(
        self,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test that Decimal values are converted to strings."""
        response = InvoiceMapper.to_response(sample_invoice, fixed_time)

        assert isinstance(response.amount, str)
        assert response.amount == "1500.00"
        assert isinstance(response.late_fee_policy_monthly_rate, str)
        assert response.late_fee_policy_monthly_rate == "0.05"

    def test_formats_dates_as_iso8601_utc(
        self,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test that dates are formatted as ISO 8601 with Z suffix."""
        response = InvoiceMapper.to_response(sample_invoice, fixed_time)

        assert response.due_date == "2024-02-15T00:00:00Z"
        assert response.created_at == "2024-01-15T12:00:00Z"
        assert response.updated_at == "2024-01-15T12:00:00Z"

    def test_computes_is_overdue_correctly_when_not_overdue(
        self,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test that is_overdue is False when invoice is not overdue."""
        # fixed_time is 2024-01-15, due_date is 2024-02-15
        response = InvoiceMapper.to_response(sample_invoice, fixed_time)

        assert response.is_overdue is False

    def test_computes_is_overdue_correctly_when_overdue(
        self,
        sample_invoice: Invoice,
    ) -> None:
        """Test that is_overdue is True when invoice is overdue."""
        # Use time after due date (2024-02-15)
        after_due = datetime(2024, 3, 1, 12, 0, 0, tzinfo=UTC)

        response = InvoiceMapper.to_response(sample_invoice, after_due)

        assert response.is_overdue is True

    def test_computes_late_fee_when_not_overdue(
        self,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test that late fee is 0.00 when not overdue."""
        response = InvoiceMapper.to_response(sample_invoice, fixed_time)

        assert response.late_fee == "0.00"

    def test_computes_late_fee_when_overdue(
        self,
        sample_invoice: Invoice,
    ) -> None:
        """Test that late fee is computed when overdue."""
        # One month after due date
        after_due = datetime(2024, 3, 16, 12, 0, 0, tzinfo=UTC)

        response = InvoiceMapper.to_response(sample_invoice, after_due)

        # 1500.00 * 0.05 = 75.00 for one month
        assert response.late_fee != "0.00"
