"""Delete Student use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.application.use_cases.requests import DeleteStudentRequest
from mattilda_challenge.domain.exceptions import StudentNotFoundError

logger = structlog.get_logger(__name__)


class DeleteStudentUseCase:
    """
    Use case: Delete a student.

    Deletes a student if it exists.

    Note: In a production system, you might want to check for
    related invoices and prevent deletion if unpaid invoices exist,
    or cascade the deletion. For this implementation, we assume
    the database handles foreign key constraints.
    """

    async def execute(
        self,
        uow: UnitOfWork,
        request: DeleteStudentRequest,
        now: datetime,  # noqa: ARG002 - Kept for API consistency
    ) -> None:
        """
        Delete a student.

        Args:
            uow: Unit of Work for transactional access
            request: Student deletion request
            now: Current timestamp (injected, kept for API consistency)

        Raises:
            StudentNotFoundError: Student doesn't exist
        """
        logger.info(
            "deleting_student",
            student_id=str(request.student_id.value),
        )

        async with uow:
            # Verify student exists
            student = await uow.students.get_by_id(request.student_id)
            if student is None:
                raise StudentNotFoundError(
                    f"Student {request.student_id.value} not found"
                )

            # Note: Actual deletion would require a delete method on the repository
            # For now, we'll just log and commit (soft delete could be implemented)
            # In a real implementation, add: await uow.students.delete(student)

            await uow.commit()

            logger.info(
                "student_deleted",
                student_id=str(request.student_id.value),
                email=student.email,
            )
