"""List Students use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import StudentFilters
from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.domain.entities import Student

logger = structlog.get_logger(__name__)


class ListStudentsUseCase:
    """
    Use case: List students with filtering and pagination.

    Returns a paginated list of students matching the provided filters.
    """

    async def execute(
        self,
        uow: UnitOfWork,
        filters: StudentFilters,
        pagination: PaginationParams,
        sort: SortParams,
        now: datetime,  # noqa: ARG002 - Kept for API consistency
    ) -> Page[Student]:
        """
        List students with filtering and pagination.

        Args:
            uow: Unit of Work for transactional access
            filters: Filter criteria (school_id, status, email)
            pagination: Offset and limit parameters
            sort: Sort field and direction
            now: Current timestamp (injected, kept for API consistency)

        Returns:
            Page containing matching students and pagination metadata
        """
        logger.debug(
            "listing_students",
            offset=pagination.offset,
            limit=pagination.limit,
            sort_by=sort.sort_by,
            sort_order=sort.sort_order,
            school_id=str(filters.school_id) if filters.school_id else None,
            status=filters.status,
        )

        async with uow:
            page = await uow.students.find(filters, pagination, sort)

            logger.debug(
                "students_listed",
                total=page.total,
                returned=len(page.items),
            )

            return page
