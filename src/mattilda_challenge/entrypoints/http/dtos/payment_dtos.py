"""Payment DTOs for HTTP layer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PaymentCreateRequestDTO(BaseModel):
    """Request to record a payment against an invoice."""

    invoice_id: str = Field(
        description="Invoice UUID to apply payment to",
        examples=["7c9e6679-7425-40de-944b-e07fc1f90ae7"],
    )
    amount: str = Field(
        description="Payment amount in MXN (decimal as string)",
        examples=["500.00", "1500.00"],
        pattern=r"^\d+\.\d{2}$",
    )
    payment_date: str = Field(
        description="Date when payment was made (ISO 8601 UTC, may be in past)",
        examples=["2024-01-20T14:30:00Z"],
    )
    payment_method: str = Field(
        min_length=1,
        max_length=50,
        description="How payment was made",
        examples=["cash", "bank_transfer", "credit_card", "debit_card", "check"],
    )
    reference_number: str | None = Field(
        default=None,
        max_length=100,
        description="External reference number (e.g., transaction ID)",
        examples=["TXN-20240120-001", "CHK-12345", None],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "invoice_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                    "amount": "500.00",
                    "payment_date": "2024-01-20T14:30:00Z",
                    "payment_method": "bank_transfer",
                    "reference_number": "TXN-20240120-001",
                },
                {
                    "invoice_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                    "amount": "1500.00",
                    "payment_date": "2024-01-20T14:30:00Z",
                    "payment_method": "cash",
                    "reference_number": None,
                },
            ]
        }
    }


class PaymentResponseDTO(BaseModel):
    """Payment entity response."""

    id: str = Field(
        description="Unique payment identifier (UUID)",
        examples=["9f8e7d6c-5b4a-3c2d-1e0f-9a8b7c6d5e4f"],
    )
    invoice_id: str = Field(
        description="Invoice UUID",
        examples=["7c9e6679-7425-40de-944b-e07fc1f90ae7"],
    )
    amount: str = Field(
        description="Payment amount in MXN",
        examples=["500.00"],
    )
    payment_date: str = Field(
        description="When payment was made (ISO 8601 UTC)",
        examples=["2024-01-20T14:30:00Z"],
    )
    payment_method: str = Field(
        description="Payment method",
        examples=["bank_transfer"],
    )
    reference_number: str | None = Field(
        description="External reference number",
        examples=["TXN-20240120-001", None],
    )
    created_at: str = Field(
        description="When payment was recorded in system (ISO 8601 UTC)",
        examples=["2024-01-20T14:35:00Z"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "9f8e7d6c-5b4a-3c2d-1e0f-9a8b7c6d5e4f",
                "invoice_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "amount": "500.00",
                "payment_date": "2024-01-20T14:30:00Z",
                "payment_method": "bank_transfer",
                "reference_number": "TXN-20240120-001",
                "created_at": "2024-01-20T14:35:00Z",
            }
        }
    }
