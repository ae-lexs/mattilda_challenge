"""Create Invoice use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.application.use_cases.requests import CreateInvoiceRequest
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.exceptions import StudentNotFoundError

logger = structlog.get_logger(__name__)


class CreateInvoiceUseCase:
    """
    Use case: Create a new invoice for a student.

    Validates:
    - Student exists

    Domain entity handles:
    - Amount validation (positive Decimal)
    - Due date validation (UTC, after created_at)
    - Late fee policy validation
    """

    async def execute(
        self,
        uow: UnitOfWork,
        request: CreateInvoiceRequest,
        now: datetime,
    ) -> Invoice:
        """
        Create invoice for student.

        Args:
            uow: Unit of Work for transactional access
            request: Invoice creation details
            now: Current timestamp (injected, never call datetime.now())

        Returns:
            Created Invoice entity

        Raises:
            StudentNotFoundError: Student doesn't exist
        """
        logger.info(
            "creating_invoice",
            student_id=str(request.student_id.value),
            amount=str(request.amount),
        )

        async with uow:
            # Validate student exists
            student = await uow.students.get_by_id(request.student_id)
            if student is None:
                raise StudentNotFoundError(
                    f"Student {request.student_id.value} not found"
                )

            # Create invoice (domain entity validates business rules)
            invoice = Invoice.create(
                student_id=request.student_id,
                amount=request.amount,
                due_date=request.due_date,
                description=request.description,
                late_fee_policy=request.late_fee_policy,
                now=now,
            )

            # Persist
            saved = await uow.invoices.save(invoice)

            # Commit
            await uow.commit()

            logger.info(
                "invoice_created",
                invoice_id=str(saved.id.value),
                student_id=str(saved.student_id.value),
                amount=str(saved.amount),
                invoice_number=saved.invoice_number,
            )

            return saved
