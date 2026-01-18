"""Get Student Account Statement use case."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import structlog

from mattilda_challenge.application.common import PaginationParams, SortParams
from mattilda_challenge.application.dtos import StudentAccountStatement
from mattilda_challenge.application.filters import InvoiceFilters
from mattilda_challenge.application.ports import (
    StudentAccountStatementCache,
    UnitOfWork,
)
from mattilda_challenge.application.use_cases.requests import (
    GetStudentAccountStatementRequest,
)
from mattilda_challenge.domain.exceptions import StudentNotFoundError
from mattilda_challenge.domain.value_objects import InvoiceStatus

logger = structlog.get_logger(__name__)


class GetStudentAccountStatementUseCase:
    """
    Use case: Get account statement for a student.

    Returns an aggregated financial summary including:
    - Total invoiced, paid, and pending amounts
    - Invoice counts by status
    - Overdue invoice count
    - Total late fees accrued

    Implements cache-aside pattern:
    1. Check cache first
    2. On cache miss, compute from database
    3. Cache the result with TTL

    Cache is optional (fail-open pattern):
    - If cache is unavailable, statement is computed fresh
    - Cache failures are logged but don't block the operation
    """

    def __init__(self, cache: StudentAccountStatementCache) -> None:
        """
        Initialize use case with cache dependency.

        Args:
            cache: Cache port for student statements (injected)
        """
        self._cache = cache

    async def execute(
        self,
        uow: UnitOfWork,
        request: GetStudentAccountStatementRequest,
        now: datetime,
    ) -> StudentAccountStatement:
        """
        Get student account statement.

        Args:
            uow: Unit of Work for transactional access
            request: Request containing student_id
            now: Current timestamp (injected)

        Returns:
            StudentAccountStatement with aggregated data

        Raises:
            StudentNotFoundError: Student doesn't exist
        """
        logger.info(
            "getting_student_account_statement",
            student_id=str(request.student_id.value),
        )

        # Try cache first
        cached = await self._cache.get(request.student_id)
        if cached is not None:
            logger.debug(
                "student_statement_cache_hit",
                student_id=str(request.student_id.value),
            )
            return cached

        logger.debug(
            "student_statement_cache_miss",
            student_id=str(request.student_id.value),
        )

        # Compute from database
        async with uow:
            # Validate student exists and get student data
            student = await uow.students.get_by_id(request.student_id)
            if student is None:
                raise StudentNotFoundError(
                    f"Student {request.student_id.value} not found"
                )

            # Get school name
            school = await uow.schools.get_by_id(student.school_id)
            school_name = school.name if school else "Unknown School"

            # Get all invoices for student (fetch all to compute counts)
            # Using large limit to get all invoices (in production, use COUNT queries)
            all_invoices_page = await uow.invoices.find(
                filters=InvoiceFilters(student_id=student.id.value),
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

            # Get total paid
            total_paid = await uow.payments.get_total_by_student(student.id)
            total_pending = total_invoiced - total_paid

            statement = StudentAccountStatement(
                student_id=student.id,
                student_name=student.full_name,
                school_name=school_name,
                total_invoiced=total_invoiced,
                total_paid=total_paid,
                total_pending=total_pending,
                invoices_pending=invoices_pending,
                invoices_partially_paid=invoices_partially_paid,
                invoices_paid=invoices_paid,
                invoices_cancelled=invoices_cancelled,
                invoices_overdue=invoices_overdue,
                total_late_fees=total_late_fees,
                statement_date=now,
            )

        # Cache the result (fail-open)
        await self._cache.set(statement)

        logger.info(
            "student_account_statement_generated",
            student_id=str(request.student_id.value),
            total_invoiced=str(total_invoiced),
            total_paid=str(total_paid),
            total_pending=str(total_pending),
        )

        return statement
