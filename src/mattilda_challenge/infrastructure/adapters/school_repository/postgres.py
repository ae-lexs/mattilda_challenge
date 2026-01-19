from __future__ import annotations

from typing import Any

from sqlalchemy import ColumnElement, and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import SchoolFilters
from mattilda_challenge.application.ports import SchoolRepository
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.infrastructure.postgres.mappers import SchoolMapper
from mattilda_challenge.infrastructure.postgres.models import SchoolModel


class PostgresSchoolRepository(SchoolRepository):
    """
    PostgreSQL implementation of SchoolRepository port.

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
        school_id: SchoolId,
        for_update: bool = False,
    ) -> School | None:
        """Get school by ID with optional row lock."""
        stmt = select(SchoolModel).where(SchoolModel.id == school_id.value)

        if for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return SchoolMapper.to_entity(model)

    async def save(self, school: School) -> School:
        """
        Save school to database.

        Uses merge() for upsert behavior, then flush() to write
        to database within current transaction.
        """
        model = SchoolMapper.to_model(school)
        merged = await self._session.merge(model)
        await self._session.flush()
        return SchoolMapper.to_entity(merged)

    async def find(
        self,
        filters: SchoolFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[School]:
        """Find schools with filters, pagination, and sorting."""
        # Build base queries
        query = select(SchoolModel)
        count_query = select(func.count()).select_from(SchoolModel)

        # Apply filters
        conditions = self._build_conditions(filters)
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Apply sorting with deterministic secondary key
        sort_column = self._get_sort_column(sort.sort_by)
        if sort.sort_order == "desc":
            query = query.order_by(sort_column.desc(), SchoolModel.id.desc())
        else:
            query = query.order_by(sort_column.asc(), SchoolModel.id.asc())

        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.limit)

        # Execute queries
        result = await self._session.execute(query)
        models = result.scalars().all()

        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()

        # Map to domain entities
        items = tuple(SchoolMapper.to_entity(m) for m in models)

        return Page(
            items=items,
            total=total,
            offset=pagination.offset,
            limit=pagination.limit,
        )

    def _build_conditions(self, filters: SchoolFilters) -> list[ColumnElement[bool]]:
        """Build SQLAlchemy filter conditions from SchoolFilters."""
        conditions: list[ColumnElement[bool]] = []

        if filters.name is not None:
            # Case-insensitive partial match
            conditions.append(SchoolModel.name.ilike(f"%{filters.name}%"))

        return conditions

    def _get_sort_column(self, sort_by: str) -> Any:
        """
        Map sort field name to SQLAlchemy column.

        NOTE: Validation of sort_by happens in the entrypoint layer (see ADR-007).
        This method provides a safe default if an invalid value reaches here,
        but this should never happen if the entrypoint validates correctly.
        """
        column_map = {
            "created_at": SchoolModel.created_at,
            "name": SchoolModel.name,
        }
        return column_map.get(sort_by, SchoolModel.created_at)

    async def delete(self, school_id: SchoolId) -> None:
        """Delete school by ID."""
        stmt = delete(SchoolModel).where(SchoolModel.id == school_id.value)
        await self._session.execute(stmt)
        await self._session.flush()
