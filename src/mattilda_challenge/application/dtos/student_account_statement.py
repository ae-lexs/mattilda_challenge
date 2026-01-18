from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal

    from mattilda_challenge.domain.value_objects import StudentId


@dataclass(frozen=True, slots=True)
class StudentAccountStatement:
    """
    Account statement for a student.

    Contains aggregated totals only (no invoice list).
    Designed to be cacheable in Redis.
    """

    student_id: StudentId
    student_name: str  # Full name (first + last)
    school_name: str

    # Aggregated totals (calculated in DB)
    total_invoiced: Decimal  # SUM(invoices.amount)
    total_paid: Decimal  # SUM(payments.amount)
    total_pending: Decimal  # total_invoiced - total_paid

    # Invoice counts by status
    invoices_pending: int
    invoices_partially_paid: int
    invoices_paid: int
    invoices_cancelled: int

    # Overdue count (calculated: now > due_date AND status in [PENDING, PARTIALLY_PAID])
    invoices_overdue: int

    # Total late fees accrued (sum of calculated late fees for overdue invoices)
    total_late_fees: Decimal

    # Metadata
    statement_date: datetime  # When statement was generated]
