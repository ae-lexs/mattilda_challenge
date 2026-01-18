# alembic/versions/002_add_indexes.py
"""Add missing indexes per ADR-004 Database Index Strategy

Revision ID: 002
Revises: 001
Create Date: 2025-01-18 12:00:00

This migration adds indexes that were not included in the initial schema
but are specified in ADR-004 Section 9 (Database Index Strategy).

Index justification (per ADR-004 Section 9.2):
- ix_payments_reference_number: Payment reconciliation lookup
  Query pattern: GET /payments?reference=TXN-123
  Used for looking up payments by external reference number during reconciliation.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add missing indexes from ADR-004 Section 9."""
    # Payments table: reference_number index for payment reconciliation
    # Query: GET /payments?reference=TXN-123
    # See ADR-004 Section 9.2 for justification
    op.create_index(
        "ix_payments_reference_number",
        "payments",
        ["reference_number"],
    )


def downgrade() -> None:
    """Remove indexes added in this migration."""
    op.drop_index("ix_payments_reference_number", table_name="payments")
