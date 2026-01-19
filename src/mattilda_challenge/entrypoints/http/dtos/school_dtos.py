"""School DTOs for HTTP layer."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SchoolCreateRequestDTO(BaseModel):
    """Request to create a new school."""

    name: str = Field(
        min_length=1,
        max_length=255,
        description="School name",
        examples=["Colegio ABC", "Escuela Primaria XYZ"],
    )
    address: str = Field(
        min_length=1,
        max_length=500,
        description="School address",
        examples=["Av. Principal 123, Ciudad de México, CDMX"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Colegio ABC",
                    "address": "Av. Principal 123, Ciudad de México, CDMX",
                },
                {
                    "name": "Escuela Primaria XYZ",
                    "address": "Calle Secundaria 456, Monterrey, NL",
                },
            ]
        }
    }


class SchoolUpdateRequestDTO(BaseModel):
    """Request to update an existing school."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="School name (optional)",
        examples=["Colegio ABC Updated"],
    )
    address: str | None = Field(
        default=None,
        min_length=1,
        max_length=500,
        description="School address (optional)",
        examples=["Nueva Av. Principal 789, Ciudad de México, CDMX"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Colegio ABC Updated",
                },
                {
                    "address": "Nueva Av. Principal 789, Ciudad de México, CDMX",
                },
                {
                    "name": "Colegio ABC Renovado",
                    "address": "Nueva Dirección 100, Guadalajara, JAL",
                },
            ]
        }
    }


class SchoolResponseDTO(BaseModel):
    """School entity response."""

    id: str = Field(
        description="Unique school identifier (UUID)",
        examples=["450e8400-e29b-41d4-a716-446655440000"],
    )
    name: str = Field(
        description="School name",
        examples=["Colegio ABC"],
    )
    address: str = Field(
        description="School address",
        examples=["Av. Principal 123, Ciudad de México, CDMX"],
    )
    created_at: str = Field(
        description="Creation timestamp (ISO 8601 UTC)",
        examples=["2024-01-15T10:30:00Z"],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "450e8400-e29b-41d4-a716-446655440000",
                "name": "Colegio ABC",
                "address": "Av. Principal 123, Ciudad de México, CDMX",
                "created_at": "2024-01-15T10:30:00Z",
            }
        }
    }
