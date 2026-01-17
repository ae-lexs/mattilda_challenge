"""Domain entities."""

from mattilda_challenge.domain.entities.invoice import Invoice, InvoiceStatus
from mattilda_challenge.domain.entities.payment import Payment
from mattilda_challenge.domain.entities.school import School
from mattilda_challenge.domain.entities.student import Student, StudentStatus

__all__ = [
    "Invoice",
    "InvoiceStatus",
    "Payment",
    "School",
    "Student",
    "StudentStatus",
]
