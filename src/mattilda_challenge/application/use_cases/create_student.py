"""Create Student use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.application.use_cases.requests import CreateStudentRequest
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.exceptions import (
    InvalidStudentDataError,
    SchoolNotFoundError,
)

logger = structlog.get_logger(__name__)


class CreateStudentUseCase:
    """
    Use case: Create a new student enrolled in a school.

    Validates:
    - School exists
    - Email is unique across all students

    Domain entity handles:
    - Name validation (non-empty)
    - Email format validation
    - UTC timestamp validation
    """

    async def execute(
        self,
        uow: UnitOfWork,
        request: CreateStudentRequest,
        now: datetime,
    ) -> Student:
        """
        Create a new student.

        Args:
            uow: Unit of Work for transactional access
            request: Student creation details
            now: Current timestamp (injected, never call datetime.now())

        Returns:
            Created Student entity

        Raises:
            SchoolNotFoundError: School doesn't exist
            InvalidStudentDataError: Email already in use
        """
        logger.info(
            "creating_student",
            school_id=str(request.school_id.value),
            email=request.email,
        )

        async with uow:
            # Validate school exists
            school = await uow.schools.get_by_id(request.school_id)
            if school is None:
                raise SchoolNotFoundError(f"School {request.school_id.value} not found")

            # Check email uniqueness
            email_exists = await uow.students.exists_by_email(request.email)
            if email_exists:
                raise InvalidStudentDataError(
                    f"Email {request.email} is already in use"
                )

            # Create student (domain entity validates business rules)
            student = Student.create(
                school_id=request.school_id,
                first_name=request.first_name,
                last_name=request.last_name,
                email=request.email,
                now=now,
            )

            # Persist
            saved = await uow.students.save(student)

            # Commit
            await uow.commit()

            logger.info(
                "student_created",
                student_id=str(saved.id.value),
                school_id=str(saved.school_id.value),
                email=saved.email,
            )

            return saved
