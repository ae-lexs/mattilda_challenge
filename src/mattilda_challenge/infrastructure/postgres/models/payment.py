from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mattilda_challenge.infrastructure.postgres.models.base import Base

if TYPE_CHECKING:
    from mattilda_challenge.infrastructure.postgres.models.invoice import InvoiceModel


class PaymentModel(Base):
    """ORM model for payments table."""

    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)

    invoice_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Payment amount (NUMERIC(12, 2))
    amount: Mapped[Decimal] = mapped_column(nullable=False)

    # Payment date: when payment was made (may differ from created_at)
    payment_date: Mapped[datetime] = mapped_column(nullable=False, index=True)

    # Payment method
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)

    # Optional reference number
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Created timestamp: when payment was recorded
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    invoice: Mapped[InvoiceModel] = relationship(back_populates="payments")

    __table_args__ = (
        Index("ix_payments_invoice_id", "invoice_id"),
        Index("ix_payments_payment_date", "payment_date"),
        Index("ix_payments_reference_number", "reference_number"),
    )
