"""Update School use case."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import structlog

from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.application.use_cases.requests import UpdateSchoolRequest
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.exceptions import SchoolNotFoundError

logger = structlog.get_logger(__name__)


class UpdateSchoolUseCase:
    """
    Use case: Update an existing school.

    Updates the specified fields of a school entity.
    Only provided fields (non-None) are updated.
    """

    async def execute(
        self,
        uow: UnitOfWork,
        request: UpdateSchoolRequest,
        now: datetime,  # noqa: ARG002 - Kept for API consistency
    ) -> School:
        """
        Update an existing school.

        Args:
            uow: Unit of Work for transactional access
            request: School update details (only non-None fields are updated)
            now: Current timestamp (injected, kept for API consistency)

        Returns:
            Updated School entity

        Raises:
            SchoolNotFoundError: School doesn't exist
        """
        logger.info(
            "updating_school",
            school_id=str(request.school_id.value),
        )

        async with uow:
            # Fetch school with row lock
            school = await uow.schools.get_by_id(
                request.school_id,
                for_update=True,
            )
            if school is None:
                raise SchoolNotFoundError(f"School {request.school_id.value} not found")

            # Apply updates using copy-on-write (explicit fields for type safety)
            updated_name = (
                request.name.strip() if request.name is not None else school.name
            )
            updated_address = (
                request.address.strip()
                if request.address is not None
                else school.address
            )

            school = replace(
                school,
                name=updated_name,
                address=updated_address,
            )

            # Persist
            saved = await uow.schools.save(school)

            # Commit
            await uow.commit()

            logger.info(
                "school_updated",
                school_id=str(saved.id.value),
                name=saved.name,
            )

            return saved
