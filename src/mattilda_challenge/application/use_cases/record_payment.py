"""Record Payment use case."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import structlog

from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.application.use_cases.requests import RecordPaymentRequest
from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.exceptions import (
    CannotPayCancelledInvoiceError,
    InvoiceNotFoundError,
    PaymentExceedsBalanceError,
)
from mattilda_challenge.domain.value_objects import InvoiceStatus

logger = structlog.get_logger(__name__)


class RecordPaymentUseCase:
    """
    Use case: Record a payment against an invoice.

    Business rules enforced:
    - Invoice must exist
    - Invoice cannot be cancelled
    - Payment cannot exceed remaining balance
    - Invoice status updated atomically with payment creation

    Transaction boundary:
    - Payment creation + invoice status update in single atomic commit
    - Row locking prevents concurrent payment race conditions
    """

    async def execute(
        self,
        uow: UnitOfWork,
        request: RecordPaymentRequest,
        now: datetime,
    ) -> Payment:
        """
        Record payment and update invoice status.

        Args:
            uow: Unit of Work for transactional access
            request: Payment details (immutable request DTO)
            now: Current timestamp (injected, never call datetime.now())

        Returns:
            Created Payment entity

        Raises:
            InvoiceNotFoundError: Invoice doesn't exist
            CannotPayCancelledInvoiceError: Invoice is cancelled
            PaymentExceedsBalanceError: Amount exceeds balance due
        """
        logger.info(
            "recording_payment",
            invoice_id=str(request.invoice_id.value),
            amount=str(request.amount),
            payment_method=request.payment_method,
        )

        async with uow:
            # 1. Fetch invoice with row lock (prevents race conditions)
            invoice = await uow.invoices.get_by_id(
                request.invoice_id,
                for_update=True,
            )
            if invoice is None:
                raise InvoiceNotFoundError(
                    f"Invoice {request.invoice_id.value} not found"
                )

            # 2. Validate business rules
            if invoice.status == InvoiceStatus.CANCELLED:
                raise CannotPayCancelledInvoiceError(
                    f"Cannot record payment for cancelled invoice {invoice.id.value}"
                )

            # 3. Calculate balance due
            # IMPORTANT: This query MUST execute within the same transaction
            # as the row lock above. The for_update=True on get_by_id ensures
            # the invoice row is locked, but get_total_by_invoice reads the
            # payments table. The adapter implementation MUST use the same
            # database session/transaction to prevent race conditions where
            # a concurrent payment is inserted between these two queries.
            total_paid = await uow.payments.get_total_by_invoice(invoice.id)
            balance_due = invoice.amount - total_paid

            if request.amount > balance_due:
                raise PaymentExceedsBalanceError(
                    f"Payment {request.amount} exceeds balance due {balance_due}"
                )

            # 4. Create payment (domain entity handles validation)
            payment = Payment.create(
                invoice_id=invoice.id,
                amount=request.amount,
                payment_date=request.payment_date,
                payment_method=request.payment_method,
                reference_number=request.reference_number,
                now=now,
            )

            # 5. Determine new invoice status
            new_balance = balance_due - request.amount
            if new_balance == Decimal("0"):
                new_status = InvoiceStatus.PAID
            else:
                new_status = InvoiceStatus.PARTIALLY_PAID

            # 6. Update invoice status (immutable - returns new instance)
            updated_invoice = invoice.update_status(new_status, now)

            # 7. Persist changes
            await uow.payments.save(payment)
            await uow.invoices.save(updated_invoice)

            # 8. Atomic commit
            await uow.commit()

            logger.info(
                "payment_recorded",
                payment_id=str(payment.id.value),
                invoice_id=str(invoice.id.value),
                amount=str(request.amount),
                new_invoice_status=new_status.value,
                remaining_balance=str(new_balance),
            )

            return payment
