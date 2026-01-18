"""Tests for Payment entity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

import pytest

from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.exceptions import (
    InvalidPaymentAmountError,
    InvalidPaymentDataError,
)
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId


class TestPaymentCreation:
    """Tests for Payment entity creation."""

    def test_create_with_valid_data(self) -> None:
        """Test creating payment with valid data."""
        payment_id = PaymentId.generate()
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        payment = Payment(
            id=payment_id,
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="bank_transfer",
            reference_number="TXN-123456",
            created_at=now,
        )

        assert payment.id == payment_id
        assert payment.invoice_id == invoice_id
        assert payment.amount == Decimal("500.00")
        assert payment.payment_date == now
        assert payment.payment_method == "bank_transfer"
        assert payment.reference_number == "TXN-123456"
        assert payment.created_at == now

    def test_create_with_none_reference_number(self) -> None:
        """Test creating payment without reference number."""
        payment_id = PaymentId.generate()
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        payment = Payment(
            id=payment_id,
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="cash",
            reference_number=None,
            created_at=now,
        )

        assert payment.reference_number is None

    def test_create_factory_method(self) -> None:
        """Test Payment.create() factory method."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)
        payment_date = now - timedelta(hours=1)

        payment = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("750.00"),
            payment_date=payment_date,
            payment_method="card",
            reference_number="CARD-789",
            now=now,
        )

        assert isinstance(payment.id, PaymentId)
        assert isinstance(payment.id.value, UUID)
        assert payment.invoice_id == invoice_id
        assert payment.amount == Decimal("750.00")
        assert payment.payment_date == payment_date
        assert payment.payment_method == "card"
        assert payment.reference_number == "CARD-789"
        assert payment.created_at == now

    def test_create_factory_strips_payment_method_whitespace(self) -> None:
        """Test Payment.create() strips payment method whitespace."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        payment = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="  bank_transfer  ",
            reference_number=None,
            now=now,
        )

        assert payment.payment_method == "bank_transfer"

    def test_create_factory_strips_reference_number_whitespace(self) -> None:
        """Test Payment.create() strips reference number whitespace."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        payment = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="bank_transfer",
            reference_number="  TXN-123  ",
            now=now,
        )

        assert payment.reference_number == "TXN-123"

    def test_create_factory_with_none_reference_number(self) -> None:
        """Test Payment.create() handles None reference number."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        payment = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="cash",
            reference_number=None,
            now=now,
        )

        assert payment.reference_number is None


class TestPaymentValidation:
    """Tests for Payment entity validation."""

    def test_non_decimal_amount_raises_error(self) -> None:
        """Test that non-Decimal amount raises InvalidPaymentAmountError."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidPaymentAmountError) as exc_info:
            Payment(
                id=PaymentId.generate(),
                invoice_id=invoice_id,
                amount=500.00,  # type: ignore[arg-type]
                payment_date=now,
                payment_method="cash",
                reference_number=None,
                created_at=now,
            )

        assert "must be Decimal" in str(exc_info.value)
        assert "float" in str(exc_info.value)

    def test_zero_amount_raises_error(self) -> None:
        """Test that zero amount raises InvalidPaymentAmountError."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidPaymentAmountError) as exc_info:
            Payment(
                id=PaymentId.generate(),
                invoice_id=invoice_id,
                amount=Decimal("0"),
                payment_date=now,
                payment_method="cash",
                reference_number=None,
                created_at=now,
            )

        assert "must be positive" in str(exc_info.value)

    def test_negative_amount_raises_error(self) -> None:
        """Test that negative amount raises InvalidPaymentAmountError."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidPaymentAmountError) as exc_info:
            Payment(
                id=PaymentId.generate(),
                invoice_id=invoice_id,
                amount=Decimal("-100.00"),
                payment_date=now,
                payment_method="cash",
                reference_number=None,
                created_at=now,
            )

        assert "must be positive" in str(exc_info.value)

    def test_empty_payment_method_raises_error(self) -> None:
        """Test that empty payment method raises InvalidPaymentDataError."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidPaymentDataError) as exc_info:
            Payment(
                id=PaymentId.generate(),
                invoice_id=invoice_id,
                amount=Decimal("500.00"),
                payment_date=now,
                payment_method="",
                reference_number=None,
                created_at=now,
            )

        assert "Payment method cannot be empty" in str(exc_info.value)

    def test_whitespace_only_payment_method_raises_error(self) -> None:
        """Test that whitespace-only payment method raises error."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidPaymentDataError) as exc_info:
            Payment(
                id=PaymentId.generate(),
                invoice_id=invoice_id,
                amount=Decimal("500.00"),
                payment_date=now,
                payment_method="   ",
                reference_number=None,
                created_at=now,
            )

        assert "Payment method cannot be empty" in str(exc_info.value)

    def test_naive_payment_date_raises_error(self) -> None:
        """Test that naive payment_date raises InvalidPaymentDataError."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)
        naive_date = datetime(2024, 1, 15, 12, 0, 0)

        with pytest.raises(InvalidPaymentDataError) as exc_info:
            Payment(
                id=PaymentId.generate(),
                invoice_id=invoice_id,
                amount=Decimal("500.00"),
                payment_date=naive_date,
                payment_method="cash",
                reference_number=None,
                created_at=now,
            )

        assert "Payment date must have UTC timezone" in str(exc_info.value)

    def test_non_utc_payment_date_raises_error(self) -> None:
        """Test that non-UTC payment_date raises InvalidPaymentDataError."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)
        eastern = timezone(timedelta(hours=-5))
        non_utc_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(InvalidPaymentDataError) as exc_info:
            Payment(
                id=PaymentId.generate(),
                invoice_id=invoice_id,
                amount=Decimal("500.00"),
                payment_date=non_utc_date,
                payment_method="cash",
                reference_number=None,
                created_at=now,
            )

        assert "Payment date must have UTC timezone" in str(exc_info.value)

    def test_naive_created_at_raises_error(self) -> None:
        """Test that naive created_at raises InvalidPaymentDataError."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)
        naive_created = datetime(2024, 1, 15, 12, 0, 0)

        with pytest.raises(InvalidPaymentDataError) as exc_info:
            Payment(
                id=PaymentId.generate(),
                invoice_id=invoice_id,
                amount=Decimal("500.00"),
                payment_date=now,
                payment_method="cash",
                reference_number=None,
                created_at=naive_created,
            )

        assert "Created timestamp must have UTC timezone" in str(exc_info.value)

    def test_non_utc_created_at_raises_error(self) -> None:
        """Test that non-UTC created_at raises InvalidPaymentDataError."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)
        eastern = timezone(timedelta(hours=-5))
        non_utc_created = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(InvalidPaymentDataError) as exc_info:
            Payment(
                id=PaymentId.generate(),
                invoice_id=invoice_id,
                amount=Decimal("500.00"),
                payment_date=now,
                payment_method="cash",
                reference_number=None,
                created_at=non_utc_created,
            )

        assert "Created timestamp must have UTC timezone" in str(exc_info.value)


class TestPaymentImmutability:
    """Tests for Payment entity immutability."""

    def test_payment_is_immutable(self) -> None:
        """Test that Payment attributes cannot be modified."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        payment = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="cash",
            reference_number=None,
            now=now,
        )

        with pytest.raises(AttributeError):
            payment.amount = Decimal("1000.00")  # type: ignore[misc]

    def test_payment_is_hashable(self) -> None:
        """Test that Payment can be used in sets and as dict keys."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        payment = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="cash",
            reference_number=None,
            now=now,
        )

        hash_value = hash(payment)
        assert isinstance(hash_value, int)

        payment_set = {payment}
        assert payment in payment_set


class TestPaymentEquality:
    """Tests for Payment entity equality."""

    def test_payments_with_same_data_are_equal(self) -> None:
        """Test that two payments with same data are equal."""
        payment_id = PaymentId.generate()
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        payment1 = Payment(
            id=payment_id,
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="cash",
            reference_number="REF-001",
            created_at=now,
        )
        payment2 = Payment(
            id=payment_id,
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="cash",
            reference_number="REF-001",
            created_at=now,
        )

        assert payment1 == payment2

    def test_payments_with_different_ids_are_not_equal(self) -> None:
        """Test that two payments with different IDs are not equal."""
        invoice_id = InvoiceId.generate()
        now = datetime.now(UTC)

        payment1 = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="cash",
            reference_number=None,
            now=now,
        )
        payment2 = Payment.create(
            invoice_id=invoice_id,
            amount=Decimal("500.00"),
            payment_date=now,
            payment_method="cash",
            reference_number=None,
            now=now,
        )

        assert payment1 != payment2
