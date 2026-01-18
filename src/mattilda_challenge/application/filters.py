from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True, slots=True)
class InvoiceFilters:
    """
    Filter parameters for invoice queries.

    All fields optional. None means no filter.
    """

    student_id: UUID | None = None
    school_id: UUID | None = None
    status: str | None = None
    due_date_from: date | None = None
    due_date_to: date | None = None


@dataclass(frozen=True, slots=True)
class StudentFilters:
    """Filter parameters for student queries."""

    school_id: UUID | None = None
    status: str | None = None
    email: str | None = None


@dataclass(frozen=True, slots=True)
class PaymentFilters:
    """Filter parameters for payment queries."""

    invoice_id: UUID | None = None
    payment_date_from: date | None = None
    payment_date_to: date | None = None


@dataclass(frozen=True, slots=True)
class SchoolFilters:
    """Filter parameters for school queries."""

    name: str | None = None
