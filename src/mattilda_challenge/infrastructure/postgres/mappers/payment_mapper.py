"""Mapper between Payment entity and PaymentModel ORM."""

from __future__ import annotations

from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId
from mattilda_challenge.infrastructure.postgres.models import PaymentModel


class PaymentMapper:
    """
    Maps between Payment entity and PaymentModel ORM.

    Responsibilities:
    - Convert PaymentId/InvoiceId value objects to/from raw UUID
    - Pass through Decimal amounts (already correct type)
    - Pass through string fields (payment_method, reference_number)
    - Pass through UTC timestamps (validated by domain)

    Stateless: All methods are static.
    """

    @staticmethod
    def to_entity(model: PaymentModel) -> Payment:
        """
        Convert ORM model to domain entity.

        Args:
            model: SQLAlchemy PaymentModel

        Returns:
            Immutable Payment entity
        """
        return Payment(
            id=PaymentId(value=model.id),
            invoice_id=InvoiceId(value=model.invoice_id),
            amount=model.amount,
            payment_date=model.payment_date,
            payment_method=model.payment_method,
            reference_number=model.reference_number,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(entity: Payment) -> PaymentModel:
        """
        Convert domain entity to ORM model.

        Args:
            entity: Immutable Payment entity

        Returns:
            Mutable PaymentModel
        """
        return PaymentModel(
            id=entity.id.value,
            invoice_id=entity.invoice_id.value,
            amount=entity.amount,
            payment_date=entity.payment_date,
            payment_method=entity.payment_method,
            reference_number=entity.reference_number,
            created_at=entity.created_at,
        )
