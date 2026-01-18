from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import InvoiceFilters
from mattilda_challenge.application.ports import InvoiceRepository
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import InvoiceId, StudentId
from mattilda_challenge.infrastructure.postgres.mappers import InvoiceMapper
from mattilda_challenge.infrastructure.postgres.models import InvoiceModel, StudentModel


class PostgresInvoiceRepository(InvoiceRepository):
    """
    PostgreSQL implementation of InvoiceRepository port.

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
        invoice_id: InvoiceId,
        for_update: bool = False,
    ) -> Invoice | None:
        """Get invoice by ID with optional row lock."""
        stmt = select(InvoiceModel).where(InvoiceModel.id == invoice_id.value)

        if for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return InvoiceMapper.to_entity(model)

    async def save(self, invoice: Invoice) -> Invoice:
        """
        Save invoice to database.

        Uses merge() for upsert behavior, then flush() to write
        to database within current transaction.
        """
        model = InvoiceMapper.to_model(invoice)
        merged = await self._session.merge(model)
        await self._session.flush()
        return InvoiceMapper.to_entity(merged)

    async def find(
        self,
        filters: InvoiceFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Invoice]:
        """Find invoices with filters, pagination, and sorting."""
        # Build base queries
        query = select(InvoiceModel)
        count_query = select(func.count()).select_from(InvoiceModel)

        # Apply filters
        conditions = self._build_conditions(filters)
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Apply sorting with deterministic secondary key
        sort_column = self._get_sort_column(sort.sort_by)
        if sort.sort_order == "desc":
            query = query.order_by(sort_column.desc(), InvoiceModel.id.desc())
        else:
            query = query.order_by(sort_column.asc(), InvoiceModel.id.asc())

        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.limit)

        # Execute queries
        result = await self._session.execute(query)
        models = result.scalars().all()

        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()

        # Map to domain entities
        items = tuple(InvoiceMapper.to_entity(m) for m in models)

        return Page(
            items=items,
            total=total,
            offset=pagination.offset,
            limit=pagination.limit,
        )

    async def find_by_student(
        self,
        student_id: StudentId,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Invoice]:
        """Find all invoices for a student (convenience method)."""
        filters = InvoiceFilters(student_id=student_id.value)
        return await self.find(filters, pagination, sort)

    async def get_total_amount_by_student(self, student_id: StudentId) -> Decimal:
        """Get sum of all invoice amounts for a student."""
        stmt = select(func.coalesce(func.sum(InvoiceModel.amount), Decimal("0"))).where(
            InvoiceModel.student_id == student_id.value
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    def _build_conditions(self, filters: InvoiceFilters) -> list[ColumnElement[bool]]:
        """Build SQLAlchemy filter conditions from InvoiceFilters."""
        conditions = []

        if filters.student_id is not None:
            conditions.append(InvoiceModel.student_id == filters.student_id)

        if filters.status is not None:
            conditions.append(InvoiceModel.status == filters.status)

        if filters.due_date_from is not None:
            conditions.append(InvoiceModel.due_date >= filters.due_date_from)

        if filters.due_date_to is not None:
            conditions.append(InvoiceModel.due_date <= filters.due_date_to)

        # school_id filter requires join through student relationship
        if filters.school_id is not None:
            conditions.append(
                InvoiceModel.student.has(StudentModel.school_id == filters.school_id)
            )

        return conditions

    def _get_sort_column(self, sort_by: str) -> Any:
        """
        Map sort field name to SQLAlchemy column.

        NOTE: Validation of sort_by happens in the entrypoint layer (see ADR-007).
        This method provides a safe default if an invalid value reaches here,
        but this should never happen if the entrypoint validates correctly.
        """
        column_map = {
            "created_at": InvoiceModel.created_at,
            "due_date": InvoiceModel.due_date,
            "amount": InvoiceModel.amount,
            "status": InvoiceModel.status,
        }
        return column_map.get(sort_by, InvoiceModel.created_at)
