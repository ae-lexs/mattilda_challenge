"""Invoice endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import InvoiceFilters
from mattilda_challenge.application.use_cases import (
    CancelInvoiceUseCase,
    CreateInvoiceUseCase,
    ListInvoicesUseCase,
)
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.exceptions import InvoiceNotFoundError
from mattilda_challenge.domain.value_objects import InvoiceId, StudentId
from mattilda_challenge.entrypoints.http.dependencies import (
    TimeProviderDep,
    UnitOfWorkDep,
)
from mattilda_challenge.entrypoints.http.dtos.common_dtos import PaginatedResponseDTO
from mattilda_challenge.entrypoints.http.dtos.invoice_dtos import (
    CancelInvoiceRequestDTO,
    InvoiceCreateRequestDTO,
    InvoiceResponseDTO,
)
from mattilda_challenge.entrypoints.http.mappers import InvoiceMapper
from mattilda_challenge.infrastructure.observability import get_logger

router = APIRouter(prefix="/invoices")
logger = get_logger(__name__)


@router.get(
    "",
    response_model=PaginatedResponseDTO[InvoiceResponseDTO],
    summary="List invoices",
    description="Get a paginated list of invoices with optional filters.",
)
async def list_invoices(
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Max items to return")] = 20,
    student_id: Annotated[str | None, Query(description="Filter by student ID")] = None,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filter by status")
    ] = None,
    sort_by: Annotated[str, Query(description="Field to sort by")] = "created_at",
    sort_order: Annotated[str, Query(description="Sort order: asc or desc")] = "desc",
) -> PaginatedResponseDTO[InvoiceResponseDTO]:
    """List invoices with pagination and filtering."""
    now = time_provider.now()

    # Parse filters - use UUID value for student_id
    parsed_student_id = StudentId.from_string(student_id).value if student_id else None
    parsed_status = status_filter.lower() if status_filter else None

    filters = InvoiceFilters(
        student_id=parsed_student_id,
        status=parsed_status,
    )

    use_case = ListInvoicesUseCase()
    result: Page[Invoice] = await use_case.execute(
        uow,
        filters,
        PaginationParams(offset=offset, limit=limit),
        SortParams(sort_by=sort_by, sort_order=sort_order),
        now,
    )

    return PaginatedResponseDTO(
        items=[InvoiceMapper.to_response(inv, now) for inv in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post(
    "",
    response_model=InvoiceResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create invoice",
    description="""
Create a new invoice for a student.

## Business Rules
- Student must exist and be ACTIVE
- Amount must be positive
- Due date must be in the future or today
- Late fee rate between 0% and 100% (0.00 to 1.00)

## Late Fee Calculation
- Fees calculated based on ORIGINAL invoice amount (not remaining balance)
- Monthly rate prorated daily (30-day month assumption)
- Fees begin accruing immediately after due date (no grace period)
- Formula: `original_amount × monthly_rate × (days_overdue / 30)`

## Invoice Number
- Human-readable format: INV-YYYY-NNNNNN (e.g., INV-2024-000042)
- Decorative only — UUID is the only authoritative identifier
    """,
    responses={
        404: {"description": "Student not found"},
        422: {"description": "Validation error"},
    },
)
async def create_invoice(
    request: InvoiceCreateRequestDTO,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> InvoiceResponseDTO:
    """Create a new invoice."""
    now = time_provider.now()

    domain_request = InvoiceMapper.to_create_request(request, now)

    use_case = CreateInvoiceUseCase()
    invoice = await use_case.execute(uow, domain_request, now)

    logger.info(
        "invoice_created",
        invoice_id=str(invoice.id.value),
        student_id=str(invoice.student_id.value),
        amount=str(invoice.amount),
    )

    return InvoiceMapper.to_response(invoice, now)


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponseDTO,
    summary="Get invoice",
    description="Get an invoice by ID.",
    responses={
        404: {"description": "Invoice not found"},
    },
)
async def get_invoice(
    invoice_id: str,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> InvoiceResponseDTO:
    """Get an invoice by ID."""
    now = time_provider.now()

    invoice = await uow.invoices.get_by_id(InvoiceId.from_string(invoice_id))
    if invoice is None:
        raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")

    return InvoiceMapper.to_response(invoice, now)


@router.post(
    "/{invoice_id}/cancel",
    response_model=InvoiceResponseDTO,
    summary="Cancel invoice",
    description="""
Cancel an invoice.

## Business Rules
- Cannot cancel paid invoices
- Requires a cancellation reason
- Status changes to CANCELLED
    """,
    responses={
        400: {"description": "Cannot cancel paid invoice"},
        404: {"description": "Invoice not found"},
    },
)
async def cancel_invoice(
    invoice_id: str,
    request: CancelInvoiceRequestDTO,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> InvoiceResponseDTO:
    """Cancel an invoice."""
    now = time_provider.now()

    domain_request = InvoiceMapper.to_cancel_request(invoice_id, request)

    use_case = CancelInvoiceUseCase()
    invoice = await use_case.execute(uow, domain_request, now)

    logger.info(
        "invoice_cancelled",
        invoice_id=str(invoice.id.value),
        reason=request.cancellation_reason,
    )

    return InvoiceMapper.to_response(invoice, now)
