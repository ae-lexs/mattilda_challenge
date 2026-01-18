from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import NUMERIC, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mattilda_challenge.infrastructure.postgres.models.base import Base

if TYPE_CHECKING:
    from mattilda_challenge.infrastructure.postgres.models.payment import PaymentModel
    from mattilda_challenge.infrastructure.postgres.models.student import StudentModel


class InvoiceModel(Base):
    """ORM model for invoices table."""

    __tablename__ = "invoices"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)

    student_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Human-readable invoice number (not unique - decorative only)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # Monetary amount (NUMERIC(12, 2) via type_annotation_map)
    amount: Mapped[Decimal] = mapped_column(nullable=False)

    # Due date
    due_date: Mapped[datetime] = mapped_column(nullable=False, index=True)

    # Description
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Late fee policy: store monthly rate
    late_fee_policy_monthly_rate: Mapped[Decimal] = mapped_column(
        NUMERIC(5, 4),  # 0.0000 to 9.9999 (supports up to 999.99%)
        nullable=False,
    )

    # Status: stored as string enum
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    student: Mapped[StudentModel] = relationship(back_populates="invoices")
    payments: Mapped[list[PaymentModel]] = relationship(
        back_populates="invoice",
        lazy="select",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_invoices_student_id", "student_id"),
        Index("ix_invoices_due_date", "due_date"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_student_status", "student_id", "status"),  # Composite
    )
