"""List Invoices use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import InvoiceFilters
from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.domain.entities import Invoice

logger = structlog.get_logger(__name__)


class ListInvoicesUseCase:
    """
    Use case: List invoices with filtering and pagination.

    Returns a paginated list of invoices matching the provided filters.
    """

    async def execute(
        self,
        uow: UnitOfWork,
        filters: InvoiceFilters,
        pagination: PaginationParams,
        sort: SortParams,
        now: datetime,  # noqa: ARG002 - Kept for API consistency
    ) -> Page[Invoice]:
        """
        List invoices with filtering and pagination.

        Args:
            uow: Unit of Work for transactional access
            filters: Filter criteria (student_id, school_id, status, due_date range)
            pagination: Offset and limit parameters
            sort: Sort field and direction
            now: Current timestamp (injected, kept for API consistency)

        Returns:
            Page containing matching invoices and pagination metadata
        """
        logger.debug(
            "listing_invoices",
            offset=pagination.offset,
            limit=pagination.limit,
            sort_by=sort.sort_by,
            sort_order=sort.sort_order,
            student_id=str(filters.student_id) if filters.student_id else None,
            school_id=str(filters.school_id) if filters.school_id else None,
            status=filters.status,
        )

        async with uow:
            page = await uow.invoices.find(filters, pagination, sort)

            logger.debug(
                "invoices_listed",
                total=page.total,
                returned=len(page.items),
            )

            return page
