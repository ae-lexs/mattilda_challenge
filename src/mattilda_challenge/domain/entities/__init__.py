"""Domain entities."""

from mattilda_challenge.domain.entities.invoice import Invoice
from mattilda_challenge.domain.entities.payment import Payment
from mattilda_challenge.domain.entities.school import School
from mattilda_challenge.domain.entities.student import Student

__all__ = [
    "Invoice",
    "Payment",
    "School",
    "Student",
]
