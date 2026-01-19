"""School mapper for DTO <-> domain model translation."""

from __future__ import annotations

from datetime import datetime

from mattilda_challenge.application.use_cases.requests import (
    CreateSchoolRequest,
    UpdateSchoolRequest,
)
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.entrypoints.http.dtos import (
    SchoolCreateRequestDTO,
    SchoolResponseDTO,
    SchoolUpdateRequestDTO,
)


class SchoolMapper:
    """Maps between School DTOs and domain models."""

    @staticmethod
    def to_create_request(dto: SchoolCreateRequestDTO) -> CreateSchoolRequest:
        """
        Convert REST DTO to domain request.

        Handles:
        - String stripping (name, address)
        """
        return CreateSchoolRequest(
            name=dto.name.strip(),
            address=dto.address.strip(),
        )

    @staticmethod
    def to_update_request(
        school_id: str,
        dto: SchoolUpdateRequestDTO,
    ) -> UpdateSchoolRequest:
        """
        Convert REST DTO to domain update request.

        Args:
            school_id: School ID from URL path
            dto: Update request DTO
        """
        return UpdateSchoolRequest(
            school_id=SchoolId.from_string(school_id),
            name=dto.name.strip() if dto.name else None,
            address=dto.address.strip() if dto.address else None,
        )

    @staticmethod
    def to_response(school: School, now: datetime) -> SchoolResponseDTO:
        """
        Convert domain entity to REST response DTO.

        Args:
            school: School entity
            now: Current timestamp (unused for schools, but consistent API)

        Returns:
            School response DTO
        """
        _ = now  # Unused for schools
        return SchoolResponseDTO(
            id=str(school.id.value),
            name=school.name,
            address=school.address,
            created_at=school.created_at.isoformat().replace("+00:00", "Z"),
        )
