from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import PaymentFilters
from mattilda_challenge.application.ports import PaymentRepository
from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId, StudentId
from mattilda_challenge.infrastructure.postgres.mappers import PaymentMapper
from mattilda_challenge.infrastructure.postgres.models import InvoiceModel, PaymentModel


class PostgresPaymentRepository(PaymentRepository):
    """
    PostgreSQL implementation of PaymentRepository port.

    Uses SQLAlchemy async session injected from UnitOfWork.
    Never calls commit() - transaction management is UoW's responsibility.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session (from UnitOfWork)
        """
        self._session = session

    async def get_by_id(
        self,
        payment_id: PaymentId,
        for_update: bool = False,
    ) -> Payment | None:
        """Get payment by ID with optional row lock."""
        stmt = select(PaymentModel).where(PaymentModel.id == payment_id.value)

        if for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return PaymentMapper.to_entity(model)

    async def save(self, payment: Payment) -> Payment:
        """
        Save payment to database.

        Uses merge() for upsert behavior, then flush() to write
        to database within current transaction.
        """
        model = PaymentMapper.to_model(payment)
        merged = await self._session.merge(model)
        await self._session.flush()
        return PaymentMapper.to_entity(merged)

    async def find(
        self,
        filters: PaymentFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Payment]:
        """Find payments with filters, pagination, and sorting."""
        # Build base queries
        query = select(PaymentModel)
        count_query = select(func.count()).select_from(PaymentModel)

        # Apply filters
        conditions = self._build_conditions(filters)
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Apply sorting with deterministic secondary key
        sort_column = self._get_sort_column(sort.sort_by)
        if sort.sort_order == "desc":
            query = query.order_by(sort_column.desc(), PaymentModel.id.desc())
        else:
            query = query.order_by(sort_column.asc(), PaymentModel.id.asc())

        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.limit)

        # Execute queries
        result = await self._session.execute(query)
        models = result.scalars().all()

        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()

        # Map to domain entities
        items = tuple(PaymentMapper.to_entity(m) for m in models)

        return Page(
            items=items,
            total=total,
            offset=pagination.offset,
            limit=pagination.limit,
        )

    async def get_total_by_invoice(self, invoice_id: InvoiceId) -> Decimal:
        """Get total payments made against an invoice."""
        stmt = select(func.coalesce(func.sum(PaymentModel.amount), Decimal("0"))).where(
            PaymentModel.invoice_id == invoice_id.value
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def get_total_by_student(self, student_id: StudentId) -> Decimal:
        """Get total payments made by a student (across all invoices)."""
        # Join through invoice to get student's payments
        stmt = (
            select(func.coalesce(func.sum(PaymentModel.amount), Decimal("0")))
            .select_from(PaymentModel)
            .join(InvoiceModel, PaymentModel.invoice_id == InvoiceModel.id)
            .where(InvoiceModel.student_id == student_id.value)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def find_by_invoice(
        self,
        invoice_id: InvoiceId,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Payment]:
        """Find all payments for an invoice (convenience method)."""
        filters = PaymentFilters(invoice_id=invoice_id.value)
        return await self.find(filters, pagination, sort)

    def _build_conditions(self, filters: PaymentFilters) -> list[ColumnElement[bool]]:
        """Build SQLAlchemy filter conditions from PaymentFilters."""
        conditions: list[ColumnElement[bool]] = []

        if filters.invoice_id is not None:
            conditions.append(PaymentModel.invoice_id == filters.invoice_id)

        if filters.payment_date_from is not None:
            conditions.append(PaymentModel.payment_date >= filters.payment_date_from)

        if filters.payment_date_to is not None:
            conditions.append(PaymentModel.payment_date <= filters.payment_date_to)

        return conditions

    def _get_sort_column(self, sort_by: str) -> Any:
        """
        Map sort field name to SQLAlchemy column.

        NOTE: Validation of sort_by happens in the entrypoint layer (see ADR-007).
        This method provides a safe default if an invalid value reaches here,
        but this should never happen if the entrypoint validates correctly.
        """
        column_map = {
            "created_at": PaymentModel.created_at,
            "payment_date": PaymentModel.payment_date,
            "amount": PaymentModel.amount,
        }
        return column_map.get(sort_by, PaymentModel.created_at)
