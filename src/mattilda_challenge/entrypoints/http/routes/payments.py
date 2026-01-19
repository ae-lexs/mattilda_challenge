"""Payment endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import PaymentFilters
from mattilda_challenge.application.use_cases import (
    ListPaymentsUseCase,
    RecordPaymentUseCase,
)
from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.exceptions import PaymentNotFoundError
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId
from mattilda_challenge.entrypoints.http.dependencies import (
    TimeProviderDep,
    UnitOfWorkDep,
)
from mattilda_challenge.entrypoints.http.dtos import (
    PaymentCreateRequestDTO,
    PaymentResponseDTO,
)
from mattilda_challenge.entrypoints.http.dtos.common_dtos import PaginatedResponseDTO
from mattilda_challenge.entrypoints.http.mappers import PaymentMapper
from mattilda_challenge.infrastructure.observability import get_logger

router = APIRouter(prefix="/payments")
logger = get_logger(__name__)


@router.get(
    "",
    response_model=PaginatedResponseDTO[PaymentResponseDTO],
    summary="List payments",
    description="Get a paginated list of payments with optional filters.",
)
async def list_payments(
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Max items to return")] = 20,
    invoice_id: Annotated[str | None, Query(description="Filter by invoice ID")] = None,
    sort_by: Annotated[str, Query(description="Field to sort by")] = "created_at",
    sort_order: Annotated[str, Query(description="Sort order: asc or desc")] = "desc",
) -> PaginatedResponseDTO[PaymentResponseDTO]:
    """List payments with pagination and filtering."""
    now = time_provider.now()

    # Parse filters - use UUID value for invoice_id
    parsed_invoice_id = InvoiceId.from_string(invoice_id).value if invoice_id else None

    filters = PaymentFilters(
        invoice_id=parsed_invoice_id,
    )

    use_case = ListPaymentsUseCase()
    result: Page[Payment] = await use_case.execute(
        uow,
        filters,
        PaginationParams(offset=offset, limit=limit),
        SortParams(sort_by=sort_by, sort_order=sort_order),
        now,
    )

    return PaginatedResponseDTO(
        items=[PaymentMapper.to_response(p) for p in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post(
    "",
    response_model=PaymentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Record payment",
    description="""
Record a payment against an invoice. Supports partial payments.

## Business Rules
- Invoice must exist and not be CANCELLED
- Payment amount must be positive
- Payment amount cannot exceed invoice balance due
- Invoice status updated atomically:
  - PENDING → PARTIALLY_PAID (first partial payment)
  - PENDING → PAID (full payment)
  - PARTIALLY_PAID → PAID (final payment)

## Partial Payments
- Multiple payments can be applied to same invoice
- Each payment is immutable (append-only audit trail)
- Balance due = invoice.amount - SUM(payments.amount)

## Atomicity
- Payment record + invoice status update in single transaction
- Uses row-level locking to prevent race conditions
- Either both succeed or both rollback
    """,
    responses={
        400: {
            "description": "Business rule violation (cancelled invoice, exceeds balance)"
        },
        404: {"description": "Invoice not found"},
        422: {"description": "Validation error (negative amount, etc.)"},
    },
)
async def record_payment(
    request: PaymentCreateRequestDTO,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> PaymentResponseDTO:
    """Record a payment against an invoice."""
    now = time_provider.now()

    domain_request = PaymentMapper.to_create_request(request, now)

    use_case = RecordPaymentUseCase()
    payment = await use_case.execute(uow, domain_request, now)

    logger.info(
        "payment_recorded",
        payment_id=str(payment.id.value),
        invoice_id=str(payment.invoice_id.value),
        amount=str(payment.amount),
    )

    return PaymentMapper.to_response(payment)


@router.get(
    "/{payment_id}",
    response_model=PaymentResponseDTO,
    summary="Get payment",
    description="Get a payment by ID.",
    responses={
        404: {"description": "Payment not found"},
    },
)
async def get_payment(
    payment_id: str,
    uow: UnitOfWorkDep,
) -> PaymentResponseDTO:
    """Get a payment by ID."""
    payment = await uow.payments.get_by_id(PaymentId.from_string(payment_id))
    if payment is None:
        raise PaymentNotFoundError(f"Payment {payment_id} not found")

    return PaymentMapper.to_response(payment)
