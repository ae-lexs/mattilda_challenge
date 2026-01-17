from __future__ import annotations

from enum import Enum


class InvoiceStatus(str, Enum):
    """
    Invoice payment status.

    Inherits from str for JSON serialization.
    """

    PENDING = "pending"  # No payments received yet
    PARTIALLY_PAID = "partially_paid"  # Some payments received, balance remaining
    PAID = "paid"  # Fully paid (sum of payments = amount)
    CANCELLED = "cancelled"  # Invoice cancelled (no payment expected)

    def __str__(self) -> str:
        """Return string value for display."""
        return self.value
