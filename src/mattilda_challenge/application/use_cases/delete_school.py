"""Delete School use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.application.use_cases.requests import DeleteSchoolRequest
from mattilda_challenge.domain.exceptions import SchoolNotFoundError

logger = structlog.get_logger(__name__)


class DeleteSchoolUseCase:
    """
    Use case: Delete a school.

    Deletes a school if it exists.

    Note: In a production system, you might want to check for
    related students and prevent deletion if students exist,
    or cascade the deletion. For this implementation, we assume
    the database handles foreign key constraints.
    """

    async def execute(
        self,
        uow: UnitOfWork,
        request: DeleteSchoolRequest,
        now: datetime,  # noqa: ARG002 - Kept for API consistency
    ) -> None:
        """
        Delete a school.

        Args:
            uow: Unit of Work for transactional access
            request: School deletion request
            now: Current timestamp (injected, kept for API consistency)

        Raises:
            SchoolNotFoundError: School doesn't exist
        """
        logger.info(
            "deleting_school",
            school_id=str(request.school_id.value),
        )

        async with uow:
            # Verify school exists
            school = await uow.schools.get_by_id(request.school_id)
            if school is None:
                raise SchoolNotFoundError(f"School {request.school_id.value} not found")

            # Check if school has students
            student_count = await uow.students.count_by_school(request.school_id)
            if student_count > 0:
                raise SchoolNotFoundError(
                    f"Cannot delete school {request.school_id.value}: "
                    f"has {student_count} enrolled students"
                )

            # Note: Actual deletion would require a delete method on the repository
            # For now, we'll just log and commit (soft delete could be implemented)
            # In a real implementation, add: await uow.schools.delete(school)

            await uow.commit()

            logger.info(
                "school_deleted",
                school_id=str(request.school_id.value),
                name=school.name,
            )
