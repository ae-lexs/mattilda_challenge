"""Create School use case."""

from __future__ import annotations

from datetime import datetime

import structlog

from mattilda_challenge.application.ports import UnitOfWork
from mattilda_challenge.application.use_cases.requests import CreateSchoolRequest
from mattilda_challenge.domain.entities import School

logger = structlog.get_logger(__name__)


class CreateSchoolUseCase:
    """
    Use case: Create a new school.

    Creates a school entity with the provided name and address.
    The school is persisted atomically within a transaction.
    """

    async def execute(
        self,
        uow: UnitOfWork,
        request: CreateSchoolRequest,
        now: datetime,
    ) -> School:
        """
        Create a new school.

        Args:
            uow: Unit of Work for transactional access
            request: School creation details
            now: Current timestamp (injected, never call datetime.now())

        Returns:
            Created School entity
        """
        logger.info(
            "creating_school",
            name=request.name,
        )

        async with uow:
            # Create school (domain entity validates business rules)
            school = School.create(
                name=request.name,
                address=request.address,
                now=now,
            )

            # Persist
            saved = await uow.schools.save(school)

            # Commit
            await uow.commit()

            logger.info(
                "school_created",
                school_id=str(saved.id.value),
                name=saved.name,
            )

            return saved
