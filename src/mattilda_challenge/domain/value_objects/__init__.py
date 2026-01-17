"""Domain value objects."""

from mattilda_challenge.domain.value_objects.entity_id import EntityId
from mattilda_challenge.domain.value_objects.invoice_id import InvoiceId
from mattilda_challenge.domain.value_objects.payment_id import PaymentId
from mattilda_challenge.domain.value_objects.school_id import SchoolId
from mattilda_challenge.domain.value_objects.student_id import StudentId

__all__ = [
    "EntityId",
    "InvoiceId",
    "PaymentId",
    "SchoolId",
    "StudentId",
]
