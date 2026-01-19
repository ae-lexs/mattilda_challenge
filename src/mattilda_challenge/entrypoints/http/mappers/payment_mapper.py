"""Payment mapper for DTO <-> domain model translation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from mattilda_challenge.application.use_cases.requests import RecordPaymentRequest
from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId
from mattilda_challenge.entrypoints.http.dtos import (
    PaymentCreateRequestDTO,
    PaymentResponseDTO,
)
from mattilda_challenge.entrypoints.http.mappers.invoice_mapper import parse_iso8601_utc


class PaymentMapper:
    """Maps between Payment DTOs and domain models."""

    @staticmethod
    def to_create_request(
        dto: PaymentCreateRequestDTO,
        now: datetime,
    ) -> RecordPaymentRequest:
        """
        Convert REST DTO to domain request.

        Handles:
        - str → Decimal (amount)
        - str → UUID → InvoiceId value object
        - str → datetime (ISO 8601 → UTC datetime)
        - Time injection (now parameter)
        """
        _ = now  # Unused here, but kept for consistency
        return RecordPaymentRequest(
            invoice_id=InvoiceId.from_string(dto.invoice_id),
            amount=Decimal(dto.amount),
            payment_date=parse_iso8601_utc(dto.payment_date),
            payment_method=dto.payment_method.strip(),
            reference_number=dto.reference_number.strip()
            if dto.reference_number
            else None,
        )

    @staticmethod
    def to_response(payment: Payment) -> PaymentResponseDTO:
        """
        Convert domain entity to REST response DTO.

        Handles:
        - UUID value objects → str
        - Decimal → str (monetary values)
        - datetime → str (ISO 8601 format)
        """
        return PaymentResponseDTO(
            id=str(payment.id.value),
            invoice_id=str(payment.invoice_id.value),
            amount=str(payment.amount),
            payment_date=payment.payment_date.isoformat().replace("+00:00", "Z"),
            payment_method=payment.payment_method,
            reference_number=payment.reference_number,
            created_at=payment.created_at.isoformat().replace("+00:00", "Z"),
        )
