from __future__ import annotations

from typing import Any

from sqlalchemy import ColumnElement, and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import StudentFilters
from mattilda_challenge.application.ports import StudentRepository
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId
from mattilda_challenge.infrastructure.postgres.mappers import StudentMapper
from mattilda_challenge.infrastructure.postgres.models import StudentModel


class PostgresStudentRepository(StudentRepository):
    """
    PostgreSQL implementation of StudentRepository port.

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
        student_id: StudentId,
        for_update: bool = False,
    ) -> Student | None:
        """Get student by ID with optional row lock."""
        stmt = select(StudentModel).where(StudentModel.id == student_id.value)

        if for_update:
            stmt = stmt.with_for_update()

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        return StudentMapper.to_entity(model)

    async def save(self, student: Student) -> Student:
        """
        Save student to database.

        Uses merge() for upsert behavior, then flush() to write
        to database within current transaction.
        """
        model = StudentMapper.to_model(student)
        merged = await self._session.merge(model)
        await self._session.flush()
        return StudentMapper.to_entity(merged)

    async def find(
        self,
        filters: StudentFilters,
        pagination: PaginationParams,
        sort: SortParams,
    ) -> Page[Student]:
        """Find students with filters, pagination, and sorting."""
        # Build base queries
        query = select(StudentModel)
        count_query = select(func.count()).select_from(StudentModel)

        # Apply filters
        conditions = self._build_conditions(filters)
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Apply sorting with deterministic secondary key
        sort_column = self._get_sort_column(sort.sort_by)
        if sort.sort_order == "desc":
            query = query.order_by(sort_column.desc(), StudentModel.id.desc())
        else:
            query = query.order_by(sort_column.asc(), StudentModel.id.asc())

        # Apply pagination
        query = query.offset(pagination.offset).limit(pagination.limit)

        # Execute queries
        result = await self._session.execute(query)
        models = result.scalars().all()

        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()

        # Map to domain entities
        items = tuple(StudentMapper.to_entity(m) for m in models)

        return Page(
            items=items,
            total=total,
            offset=pagination.offset,
            limit=pagination.limit,
        )

    async def exists_by_email(self, email: str) -> bool:
        """Check if a student with given email already exists."""
        stmt = (
            select(func.count())
            .select_from(StudentModel)
            .where(StudentModel.email == email)
        )
        result = await self._session.execute(stmt)
        count = result.scalar_one()
        return count > 0

    async def count_by_school(self, school_id: SchoolId) -> int:
        """Count students in a school."""
        stmt = (
            select(func.count())
            .select_from(StudentModel)
            .where(StudentModel.school_id == school_id.value)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    def _build_conditions(self, filters: StudentFilters) -> list[ColumnElement[bool]]:
        """Build SQLAlchemy filter conditions from StudentFilters."""
        conditions: list[ColumnElement[bool]] = []

        if filters.school_id is not None:
            conditions.append(StudentModel.school_id == filters.school_id)

        if filters.status is not None:
            conditions.append(StudentModel.status == filters.status)

        if filters.email is not None:
            conditions.append(StudentModel.email == filters.email)

        return conditions

    def _get_sort_column(self, sort_by: str) -> Any:
        """
        Map sort field name to SQLAlchemy column.

        NOTE: Validation of sort_by happens in the entrypoint layer (see ADR-007).
        This method provides a safe default if an invalid value reaches here,
        but this should never happen if the entrypoint validates correctly.
        """
        column_map = {
            "created_at": StudentModel.created_at,
            "enrollment_date": StudentModel.enrollment_date,
            "first_name": StudentModel.first_name,
            "last_name": StudentModel.last_name,
            "email": StudentModel.email,
            "status": StudentModel.status,
        }
        return column_map.get(sort_by, StudentModel.created_at)

    async def delete(self, student_id: StudentId) -> None:
        """Delete student by ID."""
        stmt = delete(StudentModel).where(StudentModel.id == student_id.value)
        await self._session.execute(stmt)
        await self._session.flush()
