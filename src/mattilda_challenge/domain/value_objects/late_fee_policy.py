from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from mattilda_challenge.domain.exceptions import InvalidLateFeeRateError
from mattilda_challenge.domain.validate_utc_timestamp import validate_utc_timestamp


@dataclass(frozen=True, slots=True)
class LateFeePolicy:
    """
    Late fee calculation policy.

    Encapsulates business rules for late fee calculation in a testable,
    reusable value object. This ensures the "original amount vs balance"
    rule is encoded once and consistent across the domain.
    """

    monthly_rate: Decimal  # e.g., Decimal("0.05") = 5% per month

    def __post_init__(self) -> None:
        """Validate policy parameters."""
        if not isinstance(self.monthly_rate, Decimal):
            raise InvalidLateFeeRateError(
                f"Monthly rate must be Decimal, got {type(self.monthly_rate).__name__}"
            )

        if self.monthly_rate < Decimal("0") or self.monthly_rate > Decimal("1"):
            raise InvalidLateFeeRateError(
                f"Monthly rate must be between 0 and 1, got {self.monthly_rate}"
            )

    def calculate_fee(
        self,
        original_amount: Decimal,
        due_date: datetime,
        now: datetime,
    ) -> Decimal:
        """
        Calculate late fee for an overdue invoice.

        **Business Rule**: Fee is based on ORIGINAL invoice amount,
        NOT the remaining balance due. This rule is encoded here once
        and reused consistently.

        Formula: original_amount × monthly_rate × (days_overdue / 30)

        Args:
            original_amount: Original invoice amount (not balance due)
            due_date: Invoice due date (must have UTC timezone)
            now: Current timestamp (must have UTC timezone, injected)

        Returns:
            Late fee amount (Decimal, rounded to cents)
            Returns Decimal("0.00") if not overdue

        Raises:
            InvalidTimestampError: If timestamps lack UTC timezone
        """
        # Validate UTC (defensive, should be caught earlier)
        validate_utc_timestamp(due_date, "due_date")
        validate_utc_timestamp(now, "now")

        if now <= due_date:
            return Decimal("0.00")

        days_overdue = (now.date() - due_date.date()).days

        # Monthly late fee based on ORIGINAL amount
        monthly_fee = original_amount * self.monthly_rate

        # Daily proration (30 days per month)
        daily_fee = monthly_fee / Decimal("30")

        # Total fee for days overdue
        total_fee = daily_fee * Decimal(str(days_overdue))

        # Explicit rounding to cents
        return total_fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def standard(cls) -> LateFeePolicy:
        """Factory method for standard 5% monthly late fee policy."""
        return cls(monthly_rate=Decimal("0.05"))

    @classmethod
    def no_late_fees(cls) -> LateFeePolicy:
        """Factory method for no late fee policy (0%)."""
        return cls(monthly_rate=Decimal("0.00"))
