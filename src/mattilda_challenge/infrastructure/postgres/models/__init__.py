"""PostgreSQL ORM models."""

from mattilda_challenge.infrastructure.postgres.models.base import Base
from mattilda_challenge.infrastructure.postgres.models.invoice import InvoiceModel
from mattilda_challenge.infrastructure.postgres.models.payment import PaymentModel
from mattilda_challenge.infrastructure.postgres.models.school import SchoolModel
from mattilda_challenge.infrastructure.postgres.models.student import StudentModel

__all__ = [
    "Base",
    "InvoiceModel",
    "PaymentModel",
    "SchoolModel",
    "StudentModel",
]
