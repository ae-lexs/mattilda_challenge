"""Mapper between Invoice entity and InvoiceModel ORM."""

from __future__ import annotations

from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    StudentId,
)
from mattilda_challenge.infrastructure.postgres.models import InvoiceModel


class InvoiceMapper:
    """
    Maps between Invoice entity and InvoiceModel ORM.

    Responsibilities:
    - Convert InvoiceId/StudentId value objects to/from raw UUID
    - Convert InvoiceStatus enum to/from string
    - Reconstruct LateFeePolicy from stored monthly_rate
    - Pass through Decimal amounts (already correct type)
    - Pass through UTC timestamps (validated by domain)

    Stateless: All methods are static.
    """

    @staticmethod
    def to_entity(model: InvoiceModel) -> Invoice:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy InvoiceModel

        Returns:
            Immutable Invoice entity
        """
        return Invoice(
            id=InvoiceId(value=model.id),
            student_id=StudentId(value=model.student_id),
            invoice_number=model.invoice_number,
            amount=model.amount,
            due_date=model.due_date,
            description=model.description,
            late_fee_policy=LateFeePolicy(
                monthly_rate=model.late_fee_policy_monthly_rate
            ),
            status=InvoiceStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: Invoice) -> InvoiceModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Immutable Invoice entity

        Returns:
            Mutable InvoiceModel
        """
        return InvoiceModel(
            id=entity.id.value,
            student_id=entity.student_id.value,
            invoice_number=entity.invoice_number,
            amount=entity.amount,
            due_date=entity.due_date,
            description=entity.description,
            late_fee_policy_monthly_rate=entity.late_fee_policy.monthly_rate,
            status=entity.status.value,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
