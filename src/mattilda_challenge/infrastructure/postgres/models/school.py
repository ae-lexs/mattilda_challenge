from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mattilda_challenge.infrastructure.postgres.models import Base, StudentModel


class SchoolModel(Base):
    """
    ORM model for schools table.

    Mutable (SQLAlchemy requirement). Domain entity is immutable.
    """

    __tablename__ = "schools"

    # Primary key: UUID
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),  # Native PostgreSQL UUID
        primary_key=True,
    )

    # School attributes
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)

    # Timestamps (automatically uses TIMESTAMP WITH TIME ZONE)
    created_at: Mapped[datetime] = mapped_column(nullable=False)

    # Relationships (lazy loading)
    students: Mapped[list[StudentModel]] = relationship(
        back_populates="school",
        lazy="select",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (Index("ix_schools_name", "name"),)
