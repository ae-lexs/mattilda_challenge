"""
Request DTOs for use cases.

All request DTOs are immutable frozen dataclasses that represent
the input data for use case operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    LateFeePolicy,
    SchoolId,
    StudentId,
    StudentStatus,
)

# =============================================================================
# School Requests
# =============================================================================


@dataclass(frozen=True, slots=True)
class CreateSchoolRequest:
    """Request to create a new school."""

    name: str
    address: str


@dataclass(frozen=True, slots=True)
class UpdateSchoolRequest:
    """Request to update an existing school."""

    school_id: SchoolId
    name: str | None = None
    address: str | None = None


@dataclass(frozen=True, slots=True)
class DeleteSchoolRequest:
    """Request to delete a school."""

    school_id: SchoolId


# =============================================================================
# Student Requests
# =============================================================================


@dataclass(frozen=True, slots=True)
class CreateStudentRequest:
    """Request to create a new student."""

    school_id: SchoolId
    first_name: str
    last_name: str
    email: str


@dataclass(frozen=True, slots=True)
class UpdateStudentRequest:
    """Request to update an existing student."""

    student_id: StudentId
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    status: StudentStatus | None = None


@dataclass(frozen=True, slots=True)
class DeleteStudentRequest:
    """Request to delete a student."""

    student_id: StudentId


# =============================================================================
# Invoice Requests
# =============================================================================


@dataclass(frozen=True, slots=True)
class CreateInvoiceRequest:
    """Request to create a new invoice."""

    student_id: StudentId
    amount: Decimal
    due_date: datetime
    description: str
    late_fee_policy: LateFeePolicy


@dataclass(frozen=True, slots=True)
class CancelInvoiceRequest:
    """Request to cancel an invoice."""

    invoice_id: InvoiceId
    cancellation_reason: str


# =============================================================================
# Payment Requests
# =============================================================================


@dataclass(frozen=True, slots=True)
class RecordPaymentRequest:
    """Request to record a payment."""

    invoice_id: InvoiceId
    amount: Decimal
    payment_date: datetime
    payment_method: str
    reference_number: str | None = None


# =============================================================================
# Account Statement Requests
# =============================================================================


@dataclass(frozen=True, slots=True)
class GetStudentAccountStatementRequest:
    """Request to get a student's account statement."""

    student_id: StudentId


@dataclass(frozen=True, slots=True)
class GetSchoolAccountStatementRequest:
    """Request to get a school's account statement."""

    school_id: SchoolId
