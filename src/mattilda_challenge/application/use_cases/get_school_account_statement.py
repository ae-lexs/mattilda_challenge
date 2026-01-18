"""Get School Account Statement use case."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import structlog

from mattilda_challenge.application.common import PaginationParams, SortParams
from mattilda_challenge.application.dtos import SchoolAccountStatement
from mattilda_challenge.application.filters import InvoiceFilters, StudentFilters
from mattilda_challenge.application.ports import SchoolAccountStatementCache, UnitOfWork
from mattilda_challenge.application.use_cases.requests import (
    GetSchoolAccountStatementRequest,
)
from mattilda_challenge.domain.exceptions import SchoolNotFoundError
from mattilda_challenge.domain.value_objects import InvoiceStatus, StudentStatus

logger = structlog.get_logger(__name__)


class GetSchoolAccountStatementUseCase:
    """
    Use case: Get account statement for a school.

    Returns an aggregated financial summary across all students including:
    - Total and active student counts
    - Total invoiced, paid, and pending amounts
    - Invoice counts by status
    - Total late fees accrued

    Implements cache-aside pattern with fail-open behavior.
    """

    def __init__(self, cache: SchoolAccountStatementCache) -> None:
        """
        Initialize use case with cache dependency.

        Args:
            cache: Cache port for school statements (injected)
        """
        self._cache = cache

    async def execute(
        self,
        uow: UnitOfWork,
        request: GetSchoolAccountStatementRequest,
        now: datetime,
    ) -> SchoolAccountStatement:
        """
        Get school account statement.

        Args:
            uow: Unit of Work for transactional access
            request: Request containing school_id
            now: Current timestamp (injected)

        Returns:
            SchoolAccountStatement with aggregated data

        Raises:
            SchoolNotFoundError: School doesn't exist
        """
        logger.info(
            "getting_school_account_statement",
            school_id=str(request.school_id.value),
        )

        # Try cache first
        cached = await self._cache.get(request.school_id)
        if cached is not None:
            logger.debug(
                "school_statement_cache_hit",
                school_id=str(request.school_id.value),
            )
            return cached

        logger.debug(
            "school_statement_cache_miss",
            school_id=str(request.school_id.value),
        )

        # Compute from database
        async with uow:
            # Validate school exists
            school = await uow.schools.get_by_id(request.school_id)
            if school is None:
                raise SchoolNotFoundError(f"School {request.school_id.value} not found")

            # Get student counts
            all_students_page = await uow.students.find(
                filters=StudentFilters(school_id=request.school_id.value),
                pagination=PaginationParams(offset=0, limit=200),
                sort=SortParams(sort_by="created_at", sort_order="desc"),
            )
            total_students = all_students_page.total
            active_students = sum(
                1 for s in all_students_page.items if s.status == StudentStatus.ACTIVE
            )

            # Get all invoices for school (via school_id filter)
            all_invoices_page = await uow.invoices.find(
                filters=InvoiceFilters(school_id=request.school_id.value),
                pagination=PaginationParams(offset=0, limit=200),
                sort=SortParams(sort_by="created_at", sort_order="desc"),
            )
            invoices = all_invoices_page.items

            # Calculate aggregates
            total_invoiced = Decimal("0")
            invoices_pending = 0
            invoices_partially_paid = 0
            invoices_paid = 0
            invoices_cancelled = 0
            invoices_overdue = 0
            total_late_fees = Decimal("0")

            for invoice in invoices:
                total_invoiced += invoice.amount

                # Count by status
                if invoice.status == InvoiceStatus.PENDING:
                    invoices_pending += 1
                elif invoice.status == InvoiceStatus.PARTIALLY_PAID:
                    invoices_partially_paid += 1
                elif invoice.status == InvoiceStatus.PAID:
                    invoices_paid += 1
                elif invoice.status == InvoiceStatus.CANCELLED:
                    invoices_cancelled += 1

                # Check if overdue
                if invoice.is_overdue(now):
                    invoices_overdue += 1
                    total_late_fees += invoice.calculate_late_fee(now)

            # Calculate total paid across all students
            # Note: In production, this would be a single aggregate query
            total_paid = Decimal("0")
            for student in all_students_page.items:
                total_paid += await uow.payments.get_total_by_student(student.id)

            total_pending = total_invoiced - total_paid

            statement = SchoolAccountStatement(
                school_id=school.id,
                school_name=school.name,
                total_students=total_students,
                active_students=active_students,
                total_invoiced=total_invoiced,
                total_paid=total_paid,
                total_pending=total_pending,
                invoices_pending=invoices_pending,
                invoices_partially_paid=invoices_partially_paid,
                invoices_paid=invoices_paid,
                invoices_overdue=invoices_overdue,
                invoices_cancelled=invoices_cancelled,
                total_late_fees=total_late_fees,
                statement_date=now,
            )

        # Cache the result (fail-open)
        await self._cache.set(statement)

        logger.info(
            "school_account_statement_generated",
            school_id=str(request.school_id.value),
            total_students=total_students,
            total_invoiced=str(total_invoiced),
            total_paid=str(total_paid),
            total_pending=str(total_pending),
        )

        return statement
