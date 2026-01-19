"""Student DTOs for HTTP layer."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class StudentCreateRequestDTO(BaseModel):
    """Request to create a new student."""

    school_id: str = Field(
        description="School UUID where student will be enrolled",
        examples=["450e8400-e29b-41d4-a716-446655440000"],
    )
    first_name: str = Field(
        min_length=1,
        max_length=100,
        description="Student's first name",
        examples=["Juan", "María"],
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
        description="Student's last name",
        examples=["Pérez", "García"],
    )
    email: EmailStr = Field(
        description="Student's email address",
        examples=["juan.perez@example.com"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "school_id": "450e8400-e29b-41d4-a716-446655440000",
                    "first_name": "Juan",
                    "last_name": "Pérez",
                    "email": "juan.perez@example.com",
                },
            ]
        }
    }


class StudentUpdateRequestDTO(BaseModel):
    """Request to update an existing student."""

    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Student's first name (optional)",
        examples=["Juan Carlos"],
    )
    last_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Student's last name (optional)",
        examples=["Pérez García"],
    )
    email: EmailStr | None = Field(
        default=None,
        description="Student's email address (optional)",
        examples=["juancarlos.perez@example.com"],
    )
    status: str | None = Field(
        default=None,
        description="Student status: active, inactive, graduated",
        examples=["active", "inactive", "graduated"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "first_name": "Juan Carlos",
                },
                {
                    "status": "graduated",
                },
                {
                    "first_name": "María",
                    "last_name": "González López",
                    "email": "maria.gonzalez@example.com",
                },
            ]
        }
    }


class StudentResponseDTO(BaseModel):
    """Student entity response."""

    id: str = Field(
        description="Unique student identifier (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    school_id: str = Field(
        description="School UUID where student is enrolled",
        examples=["450e8400-e29b-41d4-a716-446655440000"],
    )
    first_name: str = Field(
        description="Student's first name",
        examples=["Juan"],
    )
    last_name: str = Field(
        description="Student's last name",
        examples=["Pérez"],
    )
    email: str = Field(
        description="Student's email address",
        examples=["juan.perez@example.com"],
    )
    enrollment_date: str = Field(
        description="Enrollment date (ISO 8601 UTC)",
        examples=["2024-01-15T10:30:00Z"],
    )
    status: str = Field(
        description="Student status: active, inactive, graduated",
        examples=["active"],
    )
    created_at: str = Field(
        description="Creation timestamp (ISO 8601 UTC)",
        examples=["2024-01-15T10:30:00Z"],
    )
    updated_at: str = Field(
        description="Last update timestamp (ISO 8601 UTC)",
        examples=["2024-01-15T10:30:00Z"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "school_id": "450e8400-e29b-41d4-a716-446655440000",
                "first_name": "Juan",
                "last_name": "Pérez",
                "email": "juan.perez@example.com",
                "enrollment_date": "2024-01-15T10:30:00Z",
                "status": "active",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }
    }
