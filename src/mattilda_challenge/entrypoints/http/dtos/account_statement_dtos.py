"""Account statement DTOs for HTTP layer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StudentAccountStatementDTO(BaseModel):
    """Student account statement (aggregated financial summary)."""

    student_id: str = Field(
        description="Student UUID",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    student_name: str = Field(
        description="Student full name",
        examples=["Juan Pérez García"],
    )
    school_name: str = Field(
        description="School name",
        examples=["Colegio ABC"],
    )
    total_invoiced: str = Field(
        description="Total amount invoiced to student (all time)",
        examples=["4500.00"],
    )
    total_paid: str = Field(
        description="Total amount paid by student (all time)",
        examples=["1500.00"],
    )
    total_pending: str = Field(
        description="Total amount pending (invoiced - paid)",
        examples=["3000.00"],
    )
    invoices_pending: int = Field(
        description="Count of invoices with status PENDING",
        examples=[1],
    )
    invoices_partially_paid: int = Field(
        description="Count of invoices with status PARTIALLY_PAID",
        examples=[1],
    )
    invoices_paid: int = Field(
        description="Count of invoices with status PAID",
        examples=[1],
    )
    invoices_cancelled: int = Field(
        description="Count of cancelled invoices",
        examples=[0],
    )
    invoices_overdue: int = Field(
        description="Count of overdue invoices",
        examples=[1],
    )
    total_late_fees: str = Field(
        description="Total late fees accrued on overdue invoices (computed)",
        examples=["50.00"],
    )
    statement_date: str = Field(
        description="When statement was generated (ISO 8601 UTC)",
        examples=["2024-01-20T15:00:00Z"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "student_id": "550e8400-e29b-41d4-a716-446655440000",
                "student_name": "Juan Pérez García",
                "school_name": "Colegio ABC",
                "total_invoiced": "4500.00",
                "total_paid": "1500.00",
                "total_pending": "3000.00",
                "invoices_pending": 1,
                "invoices_partially_paid": 1,
                "invoices_paid": 1,
                "invoices_cancelled": 0,
                "invoices_overdue": 1,
                "total_late_fees": "50.00",
                "statement_date": "2024-01-20T15:00:00Z",
            }
        }
    }


class SchoolAccountStatementDTO(BaseModel):
    """School account statement (aggregated across all students)."""

    school_id: str = Field(
        description="School UUID",
        examples=["450e8400-e29b-41d4-a716-446655440000"],
    )
    school_name: str = Field(
        description="School name",
        examples=["Colegio ABC"],
    )
    total_students: int = Field(
        description="Total number of students (all statuses)",
        examples=[150],
    )
    active_students: int = Field(
        description="Number of active students",
        examples=[142],
    )
    total_invoiced: str = Field(
        description="Total amount invoiced across all students",
        examples=["225000.00"],
    )
    total_paid: str = Field(
        description="Total amount paid by all students",
        examples=["180000.00"],
    )
    total_pending: str = Field(
        description="Total amount pending across all students",
        examples=["45000.00"],
    )
    invoices_pending: int = Field(
        description="Count of pending invoices (all students)",
        examples=[25],
    )
    invoices_partially_paid: int = Field(
        description="Count of partially paid invoices",
        examples=[10],
    )
    invoices_paid: int = Field(
        description="Count of paid invoices",
        examples=[115],
    )
    invoices_overdue: int = Field(
        description="Count of overdue invoices (all students)",
        examples=[8],
    )
    invoices_cancelled: int = Field(
        description="Count of cancelled invoices",
        examples=[2],
    )
    total_late_fees: str = Field(
        description="Total late fees accrued across all students",
        examples=["1250.00"],
    )
    statement_date: str = Field(
        description="When statement was generated (ISO 8601 UTC)",
        examples=["2024-01-20T15:00:00Z"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "school_id": "450e8400-e29b-41d4-a716-446655440000",
                "school_name": "Colegio ABC",
                "total_students": 150,
                "active_students": 142,
                "total_invoiced": "225000.00",
                "total_paid": "180000.00",
                "total_pending": "45000.00",
                "invoices_pending": 25,
                "invoices_partially_paid": 10,
                "invoices_paid": 115,
                "invoices_overdue": 8,
                "invoices_cancelled": 2,
                "total_late_fees": "1250.00",
                "statement_date": "2024-01-20T15:00:00Z",
            }
        }
    }
