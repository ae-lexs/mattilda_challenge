from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mattilda_challenge.infrastructure.postgres.models.base import Base

if TYPE_CHECKING:
    from mattilda_challenge.infrastructure.postgres.models.invoice import InvoiceModel
    from mattilda_challenge.infrastructure.postgres.models.school import SchoolModel


class StudentModel(Base):
    """ORM model for students table."""

    __tablename__ = "students"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)

    # Foreign key to school (immutable - student cannot transfer schools)
    school_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Student attributes
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)

    # Status: stored as string enum
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    # Timestamps
    enrollment_date: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships
    school: Mapped[SchoolModel] = relationship(back_populates="students")
    invoices: Mapped[list[InvoiceModel]] = relationship(
        back_populates="student",
        lazy="select",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_students_school_id", "school_id"),
        Index("ix_students_email", "email"),
        Index("ix_students_status", "status"),
    )
