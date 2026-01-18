"""List Payments use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import PaymentFilters
from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.domain.entities import Payment

logger = structlog.get_logger(__name__)


class ListPaymentsUseCase:
    """
    Use case: List payments with filtering and pagination.

    Returns a paginated list of payments matching the provided filters.
    """

    async def execute(
        self,
        uow: UnitOfWork,
        filters: PaymentFilters,
        pagination: PaginationParams,
        sort: SortParams,
        now: datetime,  # noqa: ARG002 - Kept for API consistency
    ) -> Page[Payment]:
        """
        List payments with filtering and pagination.

        Args:
            uow: Unit of Work for transactional access
            filters: Filter criteria (invoice_id, payment_date range)
            pagination: Offset and limit parameters
            sort: Sort field and direction
            now: Current timestamp (injected, kept for API consistency)

        Returns:
            Page containing matching payments and pagination metadata
        """
        logger.debug(
            "listing_payments",
            offset=pagination.offset,
            limit=pagination.limit,
            sort_by=sort.sort_by,
            sort_order=sort.sort_order,
            invoice_id=str(filters.invoice_id) if filters.invoice_id else None,
        )

        async with uow:
            page = await uow.payments.find(filters, pagination, sort)

            logger.debug(
                "payments_listed",
                total=page.total,
                returned=len(page.items),
            )

            return page
