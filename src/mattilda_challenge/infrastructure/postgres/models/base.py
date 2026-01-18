from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import NUMERIC, TIMESTAMP, MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming convention for predictable constraint names
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    metadata = metadata

    # Type annotation map for Mapped types
    type_annotation_map = {
        datetime: TIMESTAMP(timezone=True),  # Forces TIMESTAMP WITH TIME ZONE
        Decimal: NUMERIC(12, 2),  # Default precision for monetary values
    }
