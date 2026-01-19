"""Student endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query, status

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import StudentFilters
from mattilda_challenge.application.use_cases import (
    CreateStudentUseCase,
    DeleteStudentUseCase,
    GetStudentAccountStatementUseCase,
    ListStudentsUseCase,
    UpdateStudentUseCase,
)
from mattilda_challenge.application.use_cases.requests import (
    DeleteStudentRequest,
    GetStudentAccountStatementRequest,
)
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.exceptions import StudentNotFoundError
from mattilda_challenge.domain.value_objects import SchoolId, StudentId
from mattilda_challenge.entrypoints.http.dependencies import (
    StudentCacheDep,
    TimeProviderDep,
    UnitOfWorkDep,
)
from mattilda_challenge.entrypoints.http.dtos import (
    StudentAccountStatementDTO,
    StudentCreateRequestDTO,
    StudentResponseDTO,
    StudentUpdateRequestDTO,
)
from mattilda_challenge.entrypoints.http.dtos.common_dtos import PaginatedResponseDTO
from mattilda_challenge.entrypoints.http.mappers import (
    AccountStatementMapper,
    StudentMapper,
)
from mattilda_challenge.infrastructure.observability import get_logger

router = APIRouter(prefix="/students")
logger = get_logger(__name__)


@router.get(
    "",
    response_model=PaginatedResponseDTO[StudentResponseDTO],
    summary="List students",
    description="Get a paginated list of students with optional filters.",
)
async def list_students(
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
    offset: Annotated[int, Query(ge=0, description="Number of items to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Max items to return")] = 20,
    school_id: Annotated[str | None, Query(description="Filter by school ID")] = None,
    status_filter: Annotated[
        str | None, Query(alias="status", description="Filter by status")
    ] = None,
    email: Annotated[str | None, Query(description="Filter by email")] = None,
    sort_by: Annotated[str, Query(description="Field to sort by")] = "created_at",
    sort_order: Annotated[str, Query(description="Sort order: asc or desc")] = "desc",
) -> PaginatedResponseDTO[StudentResponseDTO]:
    """List students with pagination and filtering."""
    now = time_provider.now()

    # Parse filters - use UUID value for school_id
    parsed_school_id = SchoolId.from_string(school_id).value if school_id else None
    parsed_status = status_filter.lower() if status_filter else None

    filters = StudentFilters(
        school_id=parsed_school_id,
        status=parsed_status,
        email=email,
    )

    use_case = ListStudentsUseCase()
    result: Page[Student] = await use_case.execute(
        uow,
        filters,
        PaginationParams(offset=offset, limit=limit),
        SortParams(sort_by=sort_by, sort_order=sort_order),
        now,
    )

    return PaginatedResponseDTO(
        items=[StudentMapper.to_response(s, now) for s in result.items],
        total=result.total,
        offset=result.offset,
        limit=result.limit,
    )


@router.post(
    "",
    response_model=StudentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create student",
    description="Create a new student enrolled in a school.",
    responses={
        404: {"description": "School not found"},
    },
)
async def create_student(
    request: StudentCreateRequestDTO,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> StudentResponseDTO:
    """Create a new student."""
    now = time_provider.now()

    domain_request = StudentMapper.to_create_request(request)

    use_case = CreateStudentUseCase()
    student = await use_case.execute(uow, domain_request, now)

    logger.info(
        "student_created",
        student_id=str(student.id.value),
        school_id=str(student.school_id.value),
        name=student.full_name,
    )

    return StudentMapper.to_response(student, now)


@router.get(
    "/{student_id}",
    response_model=StudentResponseDTO,
    summary="Get student",
    description="Get a student by ID.",
    responses={
        404: {"description": "Student not found"},
    },
)
async def get_student(
    student_id: str,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> StudentResponseDTO:
    """Get a student by ID."""
    now = time_provider.now()

    student = await uow.students.get_by_id(StudentId.from_string(student_id))
    if student is None:
        raise StudentNotFoundError(f"Student {student_id} not found")

    return StudentMapper.to_response(student, now)


@router.put(
    "/{student_id}",
    response_model=StudentResponseDTO,
    summary="Update student",
    description="Update an existing student.",
    responses={
        404: {"description": "Student not found"},
    },
)
async def update_student(
    student_id: str,
    request: StudentUpdateRequestDTO,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> StudentResponseDTO:
    """Update an existing student."""
    now = time_provider.now()

    domain_request = StudentMapper.to_update_request(student_id, request)

    use_case = UpdateStudentUseCase()
    student = await use_case.execute(uow, domain_request, now)

    logger.info(
        "student_updated",
        student_id=str(student.id.value),
        name=student.full_name,
    )

    return StudentMapper.to_response(student, now)


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete student",
    description="Delete a student. Cannot delete students with outstanding invoices.",
    responses={
        404: {"description": "Student not found"},
        400: {"description": "Cannot delete student with outstanding invoices"},
    },
)
async def delete_student(
    student_id: str,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
) -> None:
    """Delete a student."""
    now = time_provider.now()

    domain_request = DeleteStudentRequest(
        student_id=StudentId.from_string(student_id),
    )

    use_case = DeleteStudentUseCase()
    await use_case.execute(uow, domain_request, now)

    logger.info(
        "student_deleted",
        student_id=student_id,
    )


@router.get(
    "/{student_id}/account-statement",
    response_model=StudentAccountStatementDTO,
    summary="Get student account statement",
    description="""
Get aggregated financial summary for a student.

## Calculations
- **total_invoiced**: SUM(invoices.amount) for all student invoices
- **total_paid**: SUM(payments.amount) for all invoices
- **total_pending**: total_invoiced - total_paid
- **invoices_overdue**: COUNT WHERE now > due_date AND status IN [PENDING, PARTIALLY_PAID]
- **total_late_fees**: SUM of calculated late fees for overdue invoices

## Performance
- Cached in Redis for 5 minutes

## Use Cases
- Dashboard overview for student billing
- Parent portal account summary
- "How much does this student owe?" business question
    """,
    responses={
        404: {"description": "Student not found"},
    },
)
async def get_student_account_statement(
    student_id: str,
    uow: UnitOfWorkDep,
    time_provider: TimeProviderDep,
    cache: StudentCacheDep,
) -> StudentAccountStatementDTO:
    """Get student account statement."""
    now = time_provider.now()
    sid = StudentId.from_string(student_id)

    use_case = GetStudentAccountStatementUseCase(cache)
    request = GetStudentAccountStatementRequest(student_id=sid)
    statement = await use_case.execute(uow, request, now)

    return AccountStatementMapper.to_student_response(statement)
