"""Mappers convert between domain entities (immutable) and ORM models (mutable)."""

from mattilda_challenge.infrastructure.postgres.mappers.invoice_mapper import (
    InvoiceMapper,
)
from mattilda_challenge.infrastructure.postgres.mappers.payment_mapper import (
    PaymentMapper,
)
from mattilda_challenge.infrastructure.postgres.mappers.school_mapper import (
    SchoolMapper,
)
from mattilda_challenge.infrastructure.postgres.mappers.student_mapper import (
    StudentMapper,
)

__all__ = [
    "InvoiceMapper",
    "PaymentMapper",
    "SchoolMapper",
    "StudentMapper",
]
