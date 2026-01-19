"""Student mapper for DTO <-> domain model translation."""

from __future__ import annotations

from datetime import datetime

from mattilda_challenge.application.use_cases.requests import (
    CreateStudentRequest,
    UpdateStudentRequest,
)
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId, StudentStatus
from mattilda_challenge.entrypoints.http.dtos import (
    StudentCreateRequestDTO,
    StudentResponseDTO,
    StudentUpdateRequestDTO,
)


class StudentMapper:
    """Maps between Student DTOs and domain models."""

    @staticmethod
    def to_create_request(dto: StudentCreateRequestDTO) -> CreateStudentRequest:
        """
        Convert REST DTO to domain request.

        Handles:
        - str → UUID → SchoolId value object
        - String stripping (names, email)
        """
        return CreateStudentRequest(
            school_id=SchoolId.from_string(dto.school_id),
            first_name=dto.first_name.strip(),
            last_name=dto.last_name.strip(),
            email=dto.email.strip().lower(),
        )

    @staticmethod
    def to_update_request(
        student_id: str,
        dto: StudentUpdateRequestDTO,
    ) -> UpdateStudentRequest:
        """
        Convert REST DTO to domain update request.

        Args:
            student_id: Student ID from URL path
            dto: Update request DTO
        """
        status = None
        if dto.status:
            status = StudentStatus(dto.status.lower())

        return UpdateStudentRequest(
            student_id=StudentId.from_string(student_id),
            first_name=dto.first_name.strip() if dto.first_name else None,
            last_name=dto.last_name.strip() if dto.last_name else None,
            email=dto.email.strip().lower() if dto.email else None,
            status=status,
        )

    @staticmethod
    def to_response(student: Student, now: datetime) -> StudentResponseDTO:
        """
        Convert domain entity to REST response DTO.

        Args:
            student: Student entity
            now: Current timestamp (unused for students, but consistent API)

        Returns:
            Student response DTO
        """
        _ = now  # Unused for students
        return StudentResponseDTO(
            id=str(student.id.value),
            school_id=str(student.school_id.value),
            first_name=student.first_name,
            last_name=student.last_name,
            email=student.email,
            enrollment_date=student.enrollment_date.isoformat().replace("+00:00", "Z"),
            status=student.status.value,
            created_at=student.created_at.isoformat().replace("+00:00", "Z"),
            updated_at=student.updated_at.isoformat().replace("+00:00", "Z"),
        )
