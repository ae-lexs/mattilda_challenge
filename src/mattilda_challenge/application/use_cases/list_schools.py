"""List Schools use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import SchoolFilters
from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.domain.entities import School

logger = structlog.get_logger(__name__)


class ListSchoolsUseCase:
    """
    Use case: List schools with filtering and pagination.

    Returns a paginated list of schools matching the provided filters.
    """

    async def execute(
        self,
        uow: UnitOfWork,
        filters: SchoolFilters,
        pagination: PaginationParams,
        sort: SortParams,
        now: datetime,  # noqa: ARG002 - Kept for API consistency
    ) -> Page[School]:
        """
        List schools with filtering and pagination.

        Args:
            uow: Unit of Work for transactional access
            filters: Filter criteria (name partial match)
            pagination: Offset and limit parameters
            sort: Sort field and direction
            now: Current timestamp (injected, kept for API consistency)

        Returns:
            Page containing matching schools and pagination metadata
        """
        logger.debug(
            "listing_schools",
            offset=pagination.offset,
            limit=pagination.limit,
            sort_by=sort.sort_by,
            sort_order=sort.sort_order,
            name_filter=filters.name,
        )

        async with uow:
            page = await uow.schools.find(filters, pagination, sort)

            logger.debug(
                "schools_listed",
                total=page.total,
                returned=len(page.items),
            )

            return page
