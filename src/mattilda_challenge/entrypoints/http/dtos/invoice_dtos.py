"""Invoice DTOs for HTTP layer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InvoiceCreateRequestDTO(BaseModel):
    """Request to create a new invoice for a student."""

    student_id: str = Field(
        description="Student UUID who will be invoiced",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    amount: str = Field(
        description="Invoice amount in MXN (decimal as string, always 2 decimal places)",
        examples=["1500.00", "2350.50", "10000.00"],
        pattern=r"^\d+\.\d{2}$",
    )
    due_date: str = Field(
        description="Payment due date (ISO 8601 format, UTC)",
        examples=["2024-02-15T00:00:00Z", "2024-03-01T23:59:59Z"],
    )
    description: str = Field(
        min_length=1,
        max_length=500,
        description="Invoice description/concept",
        examples=["January 2024 Tuition", "Lab Materials Fee", "School Uniform"],
    )
    late_fee_policy_monthly_rate: str = Field(
        description="Monthly late fee rate as decimal (e.g., '0.05' for 5% monthly)",
        examples=["0.05", "0.03", "0.00"],
        pattern=r"^[01]\.\d{2,4}$",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "student_id": "550e8400-e29b-41d4-a716-446655440000",
                    "amount": "1500.00",
                    "due_date": "2024-02-15T00:00:00Z",
                    "description": "February 2024 Tuition",
                    "late_fee_policy_monthly_rate": "0.05",
                },
                {
                    "student_id": "550e8400-e29b-41d4-a716-446655440000",
                    "amount": "250.00",
                    "due_date": "2024-02-01T00:00:00Z",
                    "description": "Lab Materials Fee",
                    "late_fee_policy_monthly_rate": "0.00",
                },
            ]
        }
    }


class CancelInvoiceRequestDTO(BaseModel):
    """Request to cancel an invoice."""

    cancellation_reason: str = Field(
        min_length=1,
        max_length=500,
        description="Reason for cancellation",
        examples=["Student withdrew from school", "Invoice created in error"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "cancellation_reason": "Student withdrew from school",
            }
        }
    }


class InvoiceResponseDTO(BaseModel):
    """Invoice entity response."""

    id: str = Field(
        description="Unique invoice identifier (UUID)",
        examples=["7c9e6679-7425-40de-944b-e07fc1f90ae7"],
    )
    student_id: str = Field(
        description="Student UUID",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    invoice_number: str = Field(
        description="Human-readable invoice number (decorative, not unique)",
        examples=["INV-2024-000042"],
    )
    amount: str = Field(
        description="Invoice amount in MXN",
        examples=["1500.00"],
    )
    due_date: str = Field(
        description="Payment due date (ISO 8601 UTC)",
        examples=["2024-02-15T00:00:00Z"],
    )
    description: str = Field(
        description="Invoice description",
        examples=["February 2024 Tuition"],
    )
    late_fee_policy_monthly_rate: str = Field(
        description="Monthly late fee rate",
        examples=["0.05"],
    )
    status: str = Field(
        description="Invoice payment status",
        examples=["pending", "partially_paid", "paid", "cancelled"],
    )
    created_at: str = Field(
        description="Creation timestamp (ISO 8601 UTC)",
        examples=["2024-01-15T10:30:00Z"],
    )
    updated_at: str = Field(
        description="Last update timestamp (ISO 8601 UTC)",
        examples=["2024-01-15T10:30:00Z"],
    )
    # Computed fields (not stored)
    is_overdue: bool = Field(
        description="Whether invoice is overdue (computed from due_date and current time)",
    )
    late_fee: str = Field(
        description="Current late fee amount (computed, may be '0.00')",
        examples=["37.50", "0.00"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "student_id": "550e8400-e29b-41d4-a716-446655440000",
                "invoice_number": "INV-2024-000042",
                "amount": "1500.00",
                "due_date": "2024-02-15T00:00:00Z",
                "description": "February 2024 Tuition",
                "late_fee_policy_monthly_rate": "0.05",
                "status": "pending",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
                "is_overdue": False,
                "late_fee": "0.00",
            }
        }
    }
