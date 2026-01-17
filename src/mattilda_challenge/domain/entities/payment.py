from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from mattilda_challenge.domain.exceptions import (
    InvalidPaymentAmountError,
    InvalidPaymentDataError,
)
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId


@dataclass(frozen=True, slots=True)
class Payment:
    """
    Payment entity representing a monetary transaction against an invoice.

    Immutable and append-only (cannot be modified after creation).
    Multiple payments can be applied to a single invoice (partial payments).
    """

    id: PaymentId
    invoice_id: InvoiceId
    amount: Decimal  # Payment amount (NEVER float)
    payment_date: datetime  # When payment was made (not when recorded)
    payment_method: str  # e.g., "cash", "bank_transfer", "card"
    reference_number: str | None  # External reference (e.g., transaction ID)
    created_at: datetime  # When payment was recorded in system

    def __post_init__(self) -> None:
        """Validate invariants at construction."""
        # Check type FIRST, before any comparisons
        if not isinstance(self.amount, Decimal):
            raise InvalidPaymentAmountError(
                f"Payment amount must be Decimal, got {type(self.amount).__name__}"
            )

        if self.amount <= Decimal("0"):
            raise InvalidPaymentAmountError(
                f"Payment amount must be positive, got {self.amount}"
            )

        if not self.payment_method or not self.payment_method.strip():
            raise InvalidPaymentDataError("Payment method cannot be empty")

        if self.payment_date.tzinfo != UTC:
            raise InvalidPaymentDataError(
                f"Payment date must have UTC timezone, got {self.payment_date.tzinfo}"
            )

        if self.created_at.tzinfo != UTC:
            raise InvalidPaymentDataError(
                f"Created timestamp must have UTC timezone, got {self.created_at.tzinfo}"
            )

    @classmethod
    def create(
        cls,
        invoice_id: InvoiceId,
        amount: Decimal,
        payment_date: datetime,
        payment_method: str,
        reference_number: str | None,
        now: datetime,
    ) -> Payment:
        """
        Create new payment record.

        Args:
            invoice_id: Invoice this payment applies to
            amount: Payment amount (must be positive Decimal)
            payment_date: When payment was made (may be in past)
            payment_method: How payment was made
            reference_number: External reference (optional)
            now: Current timestamp (when recording payment)

        Returns:
            New payment instance
        """
        return cls(
            id=PaymentId.generate(),
            invoice_id=invoice_id,
            amount=amount,
            payment_date=payment_date,
            payment_method=payment_method.strip(),
            reference_number=reference_number.strip() if reference_number else None,
            created_at=now,
        )
