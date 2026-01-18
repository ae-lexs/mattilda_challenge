"""Tests for Invoice entity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.entities.invoice import InvoiceStatus
from mattilda_challenge.domain.exceptions import (
    InvalidInvoiceAmountError,
    InvalidInvoiceDataError,
    InvalidStateTransitionError,
    InvalidTimestampError,
)
from mattilda_challenge.domain.value_objects import InvoiceId, LateFeePolicy, StudentId


class TestInvoiceStatus:
    """Tests for InvoiceStatus enum."""

    def test_status_values(self) -> None:
        """Test that status enum has expected values."""
        assert InvoiceStatus.PENDING.value == "pending"
        assert InvoiceStatus.PARTIALLY_PAID.value == "partially_paid"
        assert InvoiceStatus.PAID.value == "paid"
        assert InvoiceStatus.CANCELLED.value == "cancelled"

    def test_str_returns_value(self) -> None:
        """Test that __str__ returns the enum value."""
        assert str(InvoiceStatus.PENDING) == "pending"
        assert str(InvoiceStatus.PARTIALLY_PAID) == "partially_paid"
        assert str(InvoiceStatus.PAID) == "paid"
        assert str(InvoiceStatus.CANCELLED) == "cancelled"


class TestInvoiceCreation:
    """Tests for Invoice entity creation."""

    def test_create_with_valid_data(self) -> None:
        """Test creating invoice with valid data."""
        invoice_id = InvoiceId.generate()
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)
        policy = LateFeePolicy.standard()

        invoice = Invoice(
            id=invoice_id,
            student_id=student_id,
            invoice_number="INV-2024-000001",
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition fee - January 2024",
            late_fee_policy=policy,
            status=InvoiceStatus.PENDING,
            created_at=now,
            updated_at=now,
        )

        assert invoice.id == invoice_id
        assert invoice.student_id == student_id
        assert invoice.invoice_number == "INV-2024-000001"
        assert invoice.amount == Decimal("1500.00")
        assert invoice.due_date == due_date
        assert invoice.description == "Tuition fee - January 2024"
        assert invoice.late_fee_policy == policy
        assert invoice.status == InvoiceStatus.PENDING
        assert invoice.created_at == now
        assert invoice.updated_at == now

    def test_create_factory_method(self) -> None:
        """Test Invoice.create() factory method."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)
        policy = LateFeePolicy.standard()

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition fee",
            late_fee_policy=policy,
            now=now,
        )

        assert isinstance(invoice.id, InvoiceId)
        assert isinstance(invoice.id.value, UUID)
        assert invoice.student_id == student_id
        assert invoice.invoice_number.startswith("INV-")
        assert invoice.amount == Decimal("1500.00")
        assert invoice.due_date == due_date
        assert invoice.description == "Tuition fee"
        assert invoice.late_fee_policy == policy
        assert invoice.status == InvoiceStatus.PENDING
        assert invoice.created_at == now
        assert invoice.updated_at == now

    def test_create_strips_description_whitespace(self) -> None:
        """Test Invoice.create() strips description whitespace."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="  Tuition fee  ",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        assert invoice.description == "Tuition fee"


class TestInvoiceNumberGeneration:
    """Tests for invoice number generation."""

    def test_invoice_number_format(self) -> None:
        """Test that invoice number follows expected format."""
        student_id = StudentId.generate()
        now = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        due_date = now + timedelta(days=30)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        assert invoice.invoice_number.startswith("INV-2024-")
        assert len(invoice.invoice_number) == 15  # INV-YYYY-NNNNNN


class TestInvoiceValidation:
    """Tests for Invoice entity validation."""

    def test_non_decimal_amount_raises_error(self) -> None:
        """Test that non-Decimal amount raises InvalidInvoiceAmountError."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)

        with pytest.raises(InvalidInvoiceAmountError) as exc_info:
            Invoice(
                id=InvoiceId.generate(),
                student_id=student_id,
                invoice_number="INV-2024-000001",
                amount=1500.00,  # type: ignore[arg-type]
                due_date=due_date,
                description="Tuition",
                late_fee_policy=LateFeePolicy.standard(),
                status=InvoiceStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

        assert "must be Decimal" in str(exc_info.value)

    def test_zero_amount_raises_error(self) -> None:
        """Test that zero amount raises InvalidInvoiceAmountError."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)

        with pytest.raises(InvalidInvoiceAmountError) as exc_info:
            Invoice(
                id=InvoiceId.generate(),
                student_id=student_id,
                invoice_number="INV-2024-000001",
                amount=Decimal("0"),
                due_date=due_date,
                description="Tuition",
                late_fee_policy=LateFeePolicy.standard(),
                status=InvoiceStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

        assert "must be positive" in str(exc_info.value)

    def test_negative_amount_raises_error(self) -> None:
        """Test that negative amount raises InvalidInvoiceAmountError."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)

        with pytest.raises(InvalidInvoiceAmountError) as exc_info:
            Invoice(
                id=InvoiceId.generate(),
                student_id=student_id,
                invoice_number="INV-2024-000001",
                amount=Decimal("-100.00"),
                due_date=due_date,
                description="Tuition",
                late_fee_policy=LateFeePolicy.standard(),
                status=InvoiceStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

        assert "must be positive" in str(exc_info.value)

    def test_empty_invoice_number_raises_error(self) -> None:
        """Test that empty invoice number raises InvalidInvoiceDataError."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)

        with pytest.raises(InvalidInvoiceDataError) as exc_info:
            Invoice(
                id=InvoiceId.generate(),
                student_id=student_id,
                invoice_number="",
                amount=Decimal("1500.00"),
                due_date=due_date,
                description="Tuition",
                late_fee_policy=LateFeePolicy.standard(),
                status=InvoiceStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

        assert "Invoice number cannot be empty" in str(exc_info.value)

    def test_empty_description_raises_error(self) -> None:
        """Test that empty description raises InvalidInvoiceDataError."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)

        with pytest.raises(InvalidInvoiceDataError) as exc_info:
            Invoice(
                id=InvoiceId.generate(),
                student_id=student_id,
                invoice_number="INV-2024-000001",
                amount=Decimal("1500.00"),
                due_date=due_date,
                description="",
                late_fee_policy=LateFeePolicy.standard(),
                status=InvoiceStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

        assert "description cannot be empty" in str(exc_info.value)

    def test_naive_due_date_raises_error(self) -> None:
        """Test that naive due_date raises InvalidTimestampError."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        naive_due_date = datetime(2024, 2, 15, 12, 0, 0)

        with pytest.raises(InvalidTimestampError) as exc_info:
            Invoice(
                id=InvoiceId.generate(),
                student_id=student_id,
                invoice_number="INV-2024-000001",
                amount=Decimal("1500.00"),
                due_date=naive_due_date,
                description="Tuition",
                late_fee_policy=LateFeePolicy.standard(),
                status=InvoiceStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

        assert "due_date" in str(exc_info.value)

    def test_non_utc_created_at_raises_error(self) -> None:
        """Test that non-UTC created_at raises InvalidTimestampError."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        due_date = now + timedelta(days=30)
        eastern = timezone(timedelta(hours=-5))
        non_utc_created = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(InvalidTimestampError) as exc_info:
            Invoice(
                id=InvoiceId.generate(),
                student_id=student_id,
                invoice_number="INV-2024-000001",
                amount=Decimal("1500.00"),
                due_date=due_date,
                description="Tuition",
                late_fee_policy=LateFeePolicy.standard(),
                status=InvoiceStatus.PENDING,
                created_at=non_utc_created,
                updated_at=now,
            )

        assert "created_at" in str(exc_info.value)

    def test_due_date_before_created_raises_error(self) -> None:
        """Test that due_date before created_at raises error."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        past_due_date = now - timedelta(days=1)

        with pytest.raises(InvalidInvoiceDataError) as exc_info:
            Invoice(
                id=InvoiceId.generate(),
                student_id=student_id,
                invoice_number="INV-2024-000001",
                amount=Decimal("1500.00"),
                due_date=past_due_date,
                description="Tuition",
                late_fee_policy=LateFeePolicy.standard(),
                status=InvoiceStatus.PENDING,
                created_at=now,
                updated_at=now,
            )

        assert "cannot be before creation" in str(exc_info.value)


class TestInvoiceOverdue:
    """Tests for Invoice.is_overdue method."""

    def test_not_overdue_before_due_date(self) -> None:
        """Test invoice is not overdue before due date."""
        student_id = StudentId.generate()
        now = datetime(2024, 1, 15, tzinfo=UTC)
        due_date = datetime(2024, 1, 31, tzinfo=UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        assert not invoice.is_overdue(now)

    def test_not_overdue_on_due_date(self) -> None:
        """Test invoice is not overdue on due date."""
        student_id = StudentId.generate()
        now = datetime(2024, 1, 15, tzinfo=UTC)
        due_date = datetime(2024, 1, 31, tzinfo=UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        assert not invoice.is_overdue(due_date)

    def test_overdue_after_due_date_pending(self) -> None:
        """Test pending invoice is overdue after due date."""
        student_id = StudentId.generate()
        now = datetime(2024, 1, 15, tzinfo=UTC)
        due_date = datetime(2024, 1, 31, tzinfo=UTC)
        after_due = datetime(2024, 2, 1, tzinfo=UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        assert invoice.is_overdue(after_due)

    def test_overdue_partially_paid(self) -> None:
        """Test partially paid invoice is overdue after due date."""
        student_id = StudentId.generate()
        now = datetime(2024, 1, 15, tzinfo=UTC)
        due_date = datetime(2024, 1, 31, tzinfo=UTC)
        after_due = datetime(2024, 2, 1, tzinfo=UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )
        partially_paid = invoice.update_status(InvoiceStatus.PARTIALLY_PAID, now)

        assert partially_paid.is_overdue(after_due)

    def test_not_overdue_if_paid(self) -> None:
        """Test paid invoice is not overdue even after due date."""
        student_id = StudentId.generate()
        now = datetime(2024, 1, 15, tzinfo=UTC)
        due_date = datetime(2024, 1, 31, tzinfo=UTC)
        after_due = datetime(2024, 2, 1, tzinfo=UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )
        paid = invoice.update_status(InvoiceStatus.PAID, now)

        assert not paid.is_overdue(after_due)

    def test_not_overdue_if_cancelled(self) -> None:
        """Test cancelled invoice is not overdue even after due date."""
        student_id = StudentId.generate()
        now = datetime(2024, 1, 15, tzinfo=UTC)
        due_date = datetime(2024, 1, 31, tzinfo=UTC)
        after_due = datetime(2024, 2, 1, tzinfo=UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )
        cancelled = invoice.cancel(now)

        assert not cancelled.is_overdue(after_due)


class TestInvoiceLateFee:
    """Tests for Invoice.calculate_late_fee method."""

    def test_no_late_fee_before_due_date(self) -> None:
        """Test no late fee before due date."""
        student_id = StudentId.generate()
        now = datetime(2024, 1, 15, tzinfo=UTC)
        due_date = datetime(2024, 1, 31, tzinfo=UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        assert invoice.calculate_late_fee(now) == Decimal("0.00")

    def test_late_fee_calculated_when_overdue(self) -> None:
        """Test late fee calculated when overdue."""
        student_id = StudentId.generate()
        now = datetime(2024, 1, 1, tzinfo=UTC)
        due_date = datetime(2024, 1, 15, tzinfo=UTC)
        check_date = datetime(2024, 1, 30, tzinfo=UTC)  # 15 days overdue

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),  # 5%
            now=now,
        )

        # 1500 × 0.05 / 30 × 15 = 37.50
        assert invoice.calculate_late_fee(check_date) == Decimal("37.50")

    def test_no_late_fee_if_paid(self) -> None:
        """Test no late fee for paid invoice even after due date."""
        student_id = StudentId.generate()
        now = datetime(2024, 1, 1, tzinfo=UTC)
        due_date = datetime(2024, 1, 15, tzinfo=UTC)
        check_date = datetime(2024, 1, 30, tzinfo=UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )
        paid = invoice.update_status(InvoiceStatus.PAID, now)

        assert paid.calculate_late_fee(check_date) == Decimal("0.00")


class TestInvoiceStatusTransitions:
    """Tests for Invoice status transition methods."""

    def test_update_status_pending_to_partially_paid(self) -> None:
        """Test transition from PENDING to PARTIALLY_PAID."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        later = now + timedelta(hours=1)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        updated = invoice.update_status(InvoiceStatus.PARTIALLY_PAID, later)

        assert invoice.status == InvoiceStatus.PENDING  # Original unchanged
        assert updated.status == InvoiceStatus.PARTIALLY_PAID
        assert updated.updated_at == later

    def test_update_status_pending_to_paid(self) -> None:
        """Test transition from PENDING to PAID."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        updated = invoice.update_status(InvoiceStatus.PAID, now)

        assert updated.status == InvoiceStatus.PAID

    def test_update_status_partially_paid_to_paid(self) -> None:
        """Test transition from PARTIALLY_PAID to PAID."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )
        partially_paid = invoice.update_status(InvoiceStatus.PARTIALLY_PAID, now)
        paid = partially_paid.update_status(InvoiceStatus.PAID, now)

        assert paid.status == InvoiceStatus.PAID

    def test_update_status_same_status_allowed(self) -> None:
        """Test transition to same status is allowed."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        updated = invoice.update_status(InvoiceStatus.PENDING, now)

        assert updated.status == InvoiceStatus.PENDING

    def test_update_status_paid_to_pending_raises_error(self) -> None:
        """Test transition from PAID to PENDING raises error."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )
        paid = invoice.update_status(InvoiceStatus.PAID, now)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            paid.update_status(InvoiceStatus.PENDING, now)

        assert "Cannot transition" in str(exc_info.value)

    def test_update_status_cancelled_to_paid_raises_error(self) -> None:
        """Test transition from CANCELLED to PAID raises error."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )
        cancelled = invoice.cancel(now)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            cancelled.update_status(InvoiceStatus.PAID, now)

        assert "Cannot transition" in str(exc_info.value)


class TestInvoiceCancel:
    """Tests for Invoice.cancel method."""

    def test_cancel_pending_invoice(self) -> None:
        """Test cancelling pending invoice."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)
        later = now + timedelta(hours=1)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        cancelled = invoice.cancel(later)

        assert invoice.status == InvoiceStatus.PENDING  # Original unchanged
        assert cancelled.status == InvoiceStatus.CANCELLED
        assert cancelled.updated_at == later

    def test_cancel_partially_paid_invoice(self) -> None:
        """Test cancelling partially paid invoice."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )
        partially_paid = invoice.update_status(InvoiceStatus.PARTIALLY_PAID, now)

        cancelled = partially_paid.cancel(now)

        assert cancelled.status == InvoiceStatus.CANCELLED

    def test_cancel_paid_invoice_raises_error(self) -> None:
        """Test cancelling paid invoice raises error."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )
        paid = invoice.update_status(InvoiceStatus.PAID, now)

        with pytest.raises(InvalidStateTransitionError) as exc_info:
            paid.cancel(now)

        assert "Cannot cancel paid invoice" in str(exc_info.value)


class TestInvoiceImmutability:
    """Tests for Invoice entity immutability."""

    def test_invoice_is_immutable(self) -> None:
        """Test that Invoice attributes cannot be modified."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        with pytest.raises(AttributeError):
            invoice.amount = Decimal("2000.00")  # type: ignore[misc]

    def test_invoice_is_hashable(self) -> None:
        """Test that Invoice can be used in sets and as dict keys."""
        student_id = StudentId.generate()
        now = datetime.now(UTC)

        invoice = Invoice.create(
            student_id=student_id,
            amount=Decimal("1500.00"),
            due_date=now + timedelta(days=30),
            description="Tuition",
            late_fee_policy=LateFeePolicy.standard(),
            now=now,
        )

        hash_value = hash(invoice)
        assert isinstance(hash_value, int)

        invoice_set = {invoice}
        assert invoice in invoice_set
