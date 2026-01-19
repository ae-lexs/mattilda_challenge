"""Invoice mapper for DTO <-> domain model translation."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from mattilda_challenge.application.use_cases.requests import (
    CancelInvoiceRequest,
    CreateInvoiceRequest,
)
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import InvoiceId, LateFeePolicy, StudentId
from mattilda_challenge.entrypoints.http.dtos.invoice_dtos import (
    CancelInvoiceRequestDTO,
    InvoiceCreateRequestDTO,
    InvoiceResponseDTO,
)


def parse_iso8601_utc(date_string: str) -> datetime:
    """
    Parse ISO 8601 date string to UTC datetime.

    Args:
        date_string: ISO 8601 formatted string (e.g., "2024-01-15T10:30:00Z")

    Returns:
        UTC datetime
    """
    # Handle Z suffix
    if date_string.endswith("Z"):
        date_string = date_string[:-1] + "+00:00"
    dt = datetime.fromisoformat(date_string)
    # Ensure UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


class InvoiceMapper:
    """Maps between Invoice DTOs and domain models."""

    @staticmethod
    def to_create_request(
        dto: InvoiceCreateRequestDTO,
        now: datetime,
    ) -> CreateInvoiceRequest:
        """
        Convert REST DTO to domain request.

        Handles:
        - str → Decimal (amount, late_fee_rate)
        - str → UUID → StudentId value object
        - str → datetime (ISO 8601 → UTC datetime)
        - Time injection (now parameter)
        """
        _ = now  # Unused here, but kept for consistency
        return CreateInvoiceRequest(
            student_id=StudentId.from_string(dto.student_id),
            amount=Decimal(dto.amount),
            due_date=parse_iso8601_utc(dto.due_date),
            description=dto.description.strip(),
            late_fee_policy=LateFeePolicy(
                monthly_rate=Decimal(dto.late_fee_policy_monthly_rate)
            ),
        )

    @staticmethod
    def to_cancel_request(
        invoice_id: str,
        dto: CancelInvoiceRequestDTO,
    ) -> CancelInvoiceRequest:
        """
        Convert REST DTO to domain cancel request.

        Args:
            invoice_id: Invoice ID from URL path
            dto: Cancel request DTO
        """
        return CancelInvoiceRequest(
            invoice_id=InvoiceId.from_string(invoice_id),
            cancellation_reason=dto.cancellation_reason.strip(),
        )

    @staticmethod
    def to_response(invoice: Invoice, now: datetime) -> InvoiceResponseDTO:
        """
        Convert domain entity to REST response DTO.

        Handles:
        - UUID value objects → str
        - Decimal → str (monetary values)
        - datetime → str (ISO 8601 format)
        - Computed fields (is_overdue, late_fee)
        """
        return InvoiceResponseDTO(
            id=str(invoice.id.value),
            student_id=str(invoice.student_id.value),
            invoice_number=invoice.invoice_number,
            amount=str(invoice.amount),
            due_date=invoice.due_date.isoformat().replace("+00:00", "Z"),
            description=invoice.description,
            late_fee_policy_monthly_rate=str(invoice.late_fee_policy.monthly_rate),
            status=invoice.status.value,
            created_at=invoice.created_at.isoformat().replace("+00:00", "Z"),
            updated_at=invoice.updated_at.isoformat().replace("+00:00", "Z"),
            # Computed fields
            is_overdue=invoice.is_overdue(now),
            late_fee=str(invoice.calculate_late_fee(now)),
        )
