"""Cancel Invoice use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.application.use_cases.requests import CancelInvoiceRequest
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.exceptions import InvoiceNotFoundError

logger = structlog.get_logger(__name__)


class CancelInvoiceUseCase:
    """
    Use case: Cancel an existing invoice.

    Cancels an invoice if it's not already paid.
    The domain entity validates the state transition.

    Business rules enforced:
    - Invoice must exist
    - Invoice cannot be in PAID status (validated by domain)
    """

    async def execute(
        self,
        uow: UnitOfWork,
        request: CancelInvoiceRequest,
        now: datetime,
    ) -> Invoice:
        """
        Cancel an invoice.

        Args:
            uow: Unit of Work for transactional access
            request: Invoice cancellation details
            now: Current timestamp (injected, never call datetime.now())

        Returns:
            Cancelled Invoice entity

        Raises:
            InvoiceNotFoundError: Invoice doesn't exist
            InvalidStateTransitionError: Invoice is already paid
        """
        logger.info(
            "cancelling_invoice",
            invoice_id=str(request.invoice_id.value),
            reason=request.cancellation_reason,
        )

        async with uow:
            # Fetch invoice with row lock
            invoice = await uow.invoices.get_by_id(
                request.invoice_id,
                for_update=True,
            )
            if invoice is None:
                raise InvoiceNotFoundError(
                    f"Invoice {request.invoice_id.value} not found"
                )

            # Cancel invoice (domain validates state transition)
            cancelled_invoice = invoice.cancel(now)

            # Persist
            saved = await uow.invoices.save(cancelled_invoice)

            # Commit
            await uow.commit()

            logger.info(
                "invoice_cancelled",
                invoice_id=str(saved.id.value),
                student_id=str(saved.student_id.value),
                reason=request.cancellation_reason,
            )

            return saved
