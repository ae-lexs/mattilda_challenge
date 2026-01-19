"""Common DTOs shared across entities."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponseDTO(BaseModel):
    """Standard error response."""

    detail: str = Field(description="Error message")

    model_config = {
        "json_schema_extra": {
            "example": {"detail": "Resource not found"},
        },
    }


class PaginatedResponseDTO[T](BaseModel):
    """Generic paginated response wrapper."""

    items: list[T] = Field(description="List of items")
    total: int = Field(description="Total number of items")
    offset: int = Field(description="Current offset")
    limit: int = Field(description="Maximum items per page")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 0,
                "offset": 0,
                "limit": 20,
            },
        },
    }
