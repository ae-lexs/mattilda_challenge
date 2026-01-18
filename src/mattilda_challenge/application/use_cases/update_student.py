"""Update Student use case."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import structlog

from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.application.use_cases.requests import UpdateStudentRequest
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.exceptions import (
    InvalidStudentDataError,
    StudentNotFoundError,
)

logger = structlog.get_logger(__name__)


class UpdateStudentUseCase:
    """
    Use case: Update an existing student.

    Updates the specified fields of a student entity.
    Only provided fields (non-None) are updated.

    Note: school_id cannot be changed (immutable relationship).
    """

    async def execute(
        self,
        uow: UnitOfWork,
        request: UpdateStudentRequest,
        now: datetime,
    ) -> Student:
        """
        Update an existing student.

        Args:
            uow: Unit of Work for transactional access
            request: Student update details (only non-None fields are updated)
            now: Current timestamp (injected)

        Returns:
            Updated Student entity

        Raises:
            StudentNotFoundError: Student doesn't exist
            InvalidStudentDataError: Email already in use by another student
        """
        logger.info(
            "updating_student",
            student_id=str(request.student_id.value),
        )

        async with uow:
            # Fetch student with row lock
            student = await uow.students.get_by_id(
                request.student_id,
                for_update=True,
            )
            if student is None:
                raise StudentNotFoundError(
                    f"Student {request.student_id.value} not found"
                )

            # Check email uniqueness if changing email
            if request.email is not None and request.email != student.email:
                email_exists = await uow.students.exists_by_email(request.email)
                if email_exists:
                    raise InvalidStudentDataError(
                        f"Email {request.email} is already in use"
                    )

            # Apply updates using copy-on-write (explicit fields for type safety)
            updated_first_name = (
                request.first_name.strip()
                if request.first_name is not None
                else student.first_name
            )
            updated_last_name = (
                request.last_name.strip()
                if request.last_name is not None
                else student.last_name
            )
            updated_email = (
                request.email.strip().lower()
                if request.email is not None
                else student.email
            )
            updated_status = (
                request.status if request.status is not None else student.status
            )

            student = replace(
                student,
                first_name=updated_first_name,
                last_name=updated_last_name,
                email=updated_email,
                status=updated_status,
                updated_at=now,
            )

            # Persist
            saved = await uow.students.save(student)

            # Commit
            await uow.commit()

            logger.info(
                "student_updated",
                student_id=str(saved.id.value),
                email=saved.email,
            )

            return saved
