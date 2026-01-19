"""School endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import SchoolFilters
from mattilda_challenge.application.use_cases import (
    CreateSchoolUseCase,
    DeleteSchoolUseCase,
    GetSchoolAccountStatementUseCase,
    ListSchoolsUseCase,
    UpdateSchoolUseCase,
)
from mattilda_challenge.application.use_cases.requests import (
    DeleteSchoolRequest,
    GetSchoolAccountStatementRequest,
)
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.exceptions import SchoolNotFoundError
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.entrypoints.http.dependencies import (
    SchoolCacheDep,
    TimeProviderDep,
    UnitOfWorkDep,
)
from mattilda_challenge.entrypoints.http.dtos import (
    SchoolAccountStatementDTO,
    SchoolCreateRequestDTO,
    SchoolResponseDTO,
    SchoolUpdateRequestDTO,
)
from mattilda_challenge.entrypoints.http.dtos.common_dtos import PaginatedResponseDTO
from mattilda_challenge.entrypoints.http.mappers import (
    AccountStatementMapper,
    SchoolMapper,
)
from mattilda_challenge.infrastructure.observability import get_logger

router = APIRouter(prefix="/schools")
logger = get_logger(__name__)


@router.get(
    "",
    response_model=PaginatedResponseDTO[SchoolResponseDTO],
    summary="List schools",
    description="Get a paginated list of schools with optional filters.",
)
async def list_schools(
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Max items to return")] = 20,
    name: Annotated[str | None, Query(description="Filter by name (contains)")] = None,
    sort_by: Annotated[str, Query(description="Field to sort by")] = "created_at",
    sort_order: Annotated[str, Query(description="Sort order: asc or desc")] = "desc",
) -> PaginatedResponseDTO[SchoolResponseDTO]:
    """List schools with pagination and filtering."""
    now = time_provider.now()

    use_case = ListSchoolsUseCase()
    result: Page[School] = await use_case.execute(
        uow,
        SchoolFilters(name=name),
        PaginationParams(offset=offset, limit=limit),
        SortParams(sort_by=sort_by, sort_order=sort_order),
        now,
    )

    return PaginatedResponseDTO(
        items=[SchoolMapper.to_response(s, now) for s in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post(
    "",
    response_model=SchoolResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create school",
    description="Create a new school.",
)
async def create_school(
    request: SchoolCreateRequestDTO,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> SchoolResponseDTO:
    """Create a new school."""
    now = time_provider.now()

    domain_request = SchoolMapper.to_create_request(request)

    use_case = CreateSchoolUseCase()
    school = await use_case.execute(uow, domain_request, now)

    logger.info(
        "school_created",
        school_id=str(school.id.value),
        name=school.name,
    )

    return SchoolMapper.to_response(school, now)


@router.get(
    "/{school_id}",
    response_model=SchoolResponseDTO,
    summary="Get school",
    description="Get a school by ID.",
    responses={
        404: {"description": "School not found"},
    },
)
async def get_school(
    school_id: str,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> SchoolResponseDTO:
    """Get a school by ID."""
    now = time_provider.now()

    school = await uow.schools.get_by_id(SchoolId.from_string(school_id))
    if school is None:
        raise SchoolNotFoundError(f"School {school_id} not found")

    return SchoolMapper.to_response(school, now)


@router.put(
    "/{school_id}",
    response_model=SchoolResponseDTO,
    summary="Update school",
    description="Update an existing school.",
    responses={
        404: {"description": "School not found"},
    },
)
async def update_school(
    school_id: str,
    request: SchoolUpdateRequestDTO,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> SchoolResponseDTO:
    """Update an existing school."""
    now = time_provider.now()

    domain_request = SchoolMapper.to_update_request(school_id, request)

    use_case = UpdateSchoolUseCase()
    school = await use_case.execute(uow, domain_request, now)

    logger.info(
        "school_updated",
        school_id=str(school.id.value),
        name=school.name,
    )

    return SchoolMapper.to_response(school, now)


@router.delete(
    "/{school_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete school",
    description="Delete a school. Cannot delete schools with enrolled students.",
    responses={
        404: {"description": "School not found"},
        400: {"description": "Cannot delete school with enrolled students"},
    },
)
async def delete_school(
    school_id: str,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> None:
    """Delete a school."""
    now = time_provider.now()

    domain_request = DeleteSchoolRequest(
        school_id=SchoolId.from_string(school_id),
    )

    use_case = DeleteSchoolUseCase()
    await use_case.execute(uow, domain_request, now)

    logger.info(
        "school_deleted",
        school_id=school_id,
    )


@router.get(
    "/{school_id}/account-statement",
    response_model=SchoolAccountStatementDTO,
    summary="Get school account statement",
    description="""
Get aggregated financial summary for a school (all students).

## Business Questions Answered
- ¿Cuántos alumnos tiene un colegio? (total_students, active_students)
- ¿Cuánto le deben todos los estudiantes? (total_pending)
- ¿Cuál es el estado de cuenta del colegio? (full summary)

## Calculations
- Aggregates across ALL students in the school
- Same calculation rules as student account statement
- Includes student count by status

## Performance
- Cached in Redis for 5 minutes
    """,
    responses={
        404: {"description": "School not found"},
    },
)
async def get_school_account_statement(
    school_id: str,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
    cache: SchoolCacheDep,
) -> SchoolAccountStatementDTO:
    """Get school account statement."""
    now = time_provider.now()
    sid = SchoolId.from_string(school_id)

    use_case = GetSchoolAccountStatementUseCase(cache)
    request = GetSchoolAccountStatementRequest(school_id=sid)
    statement = await use_case.execute(uow, request, now)

    return AccountStatementMapper.to_school_response(statement)
