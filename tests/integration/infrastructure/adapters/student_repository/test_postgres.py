"""Integration tests for PostgresStudentRepository.

These tests verify the PostgreSQL repository implementation against
a real database. They test SQL query correctness and database interactions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.common import PaginationParams, SortParams
from mattilda_challenge.application.filters import StudentFilters
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId, StudentStatus
from mattilda_challenge.infrastructure.adapters.student_repository import (
    PostgresStudentRepository,
)
from mattilda_challenge.infrastructure.postgres.models import SchoolModel, StudentModel

pytestmark = pytest.mark.integration


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def student_repository(db_session: AsyncSession) -> PostgresStudentRepository:
    """Provide PostgresStudentRepository instance."""
    return PostgresStudentRepository(db_session)


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_school_id() -> SchoolId:
    """Provide fixed school ID for testing."""
    return SchoolId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def fixed_school_id_2() -> SchoolId:
    """Provide second fixed school ID for testing."""
    return SchoolId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))


@pytest.fixture
def fixed_student_id_2() -> StudentId:
    """Provide second fixed student ID for testing."""
    return StudentId(value=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))


@pytest.fixture
def fixed_student_id_3() -> StudentId:
    """Provide third fixed student ID for testing."""
    return StudentId(value=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))


@pytest.fixture
async def saved_school(
    db_session: AsyncSession,
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> SchoolModel:
    """Insert a school into the test database."""
    school = SchoolModel(
        id=fixed_school_id.value,
        name="Test School",
        address="123 Test Street",
        created_at=fixed_time,
    )
    db_session.add(school)
    await db_session.flush()
    return school


@pytest.fixture
async def saved_school_2(
    db_session: AsyncSession,
    fixed_school_id_2: SchoolId,
    fixed_time: datetime,
) -> SchoolModel:
    """Insert second school into the test database."""
    school = SchoolModel(
        id=fixed_school_id_2.value,
        name="Second School",
        address="456 Other Avenue",
        created_at=fixed_time,
    )
    db_session.add(school)
    await db_session.flush()
    return school


@pytest.fixture
async def saved_student(
    db_session: AsyncSession,
    saved_school: SchoolModel,
    fixed_student_id: StudentId,
    fixed_time: datetime,
) -> StudentModel:
    """Insert a student into the test database."""
    student = StudentModel(
        id=fixed_student_id.value,
        school_id=saved_school.id,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        status="active",
        enrollment_date=fixed_time,
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    db_session.add(student)
    await db_session.flush()
    return student


@pytest.fixture
async def saved_student_2(
    db_session: AsyncSession,
    saved_school: SchoolModel,
    fixed_student_id_2: StudentId,
    fixed_time: datetime,
) -> StudentModel:
    """Insert second student (same school) into the test database."""
    student = StudentModel(
        id=fixed_student_id_2.value,
        school_id=saved_school.id,
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        status="inactive",
        enrollment_date=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
        created_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
    )
    db_session.add(student)
    await db_session.flush()
    return student


@pytest.fixture
async def saved_student_3(
    db_session: AsyncSession,
    saved_school_2: SchoolModel,
    fixed_student_id_3: StudentId,
    fixed_time: datetime,
) -> StudentModel:
    """Insert third student (different school) into the test database."""
    student = StudentModel(
        id=fixed_student_id_3.value,
        school_id=saved_school_2.id,
        first_name="Bob",
        last_name="Johnson",
        email="bob.johnson@example.com",
        status="graduated",
        enrollment_date=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
        created_at=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
    )
    db_session.add(student)
    await db_session.flush()
    return student


@pytest.fixture
def sample_student(
    fixed_student_id: StudentId,
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> Student:
    """Create a sample Student domain entity."""
    return Student(
        id=fixed_student_id,
        school_id=fixed_school_id,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        enrollment_date=fixed_time,
        status=StudentStatus.ACTIVE,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


# ============================================================================
# get_by_id Tests
# ============================================================================


class TestPostgresStudentRepositoryGetById:
    """Tests for get_by_id method."""

    async def test_returns_student_when_exists(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        fixed_student_id: StudentId,
    ) -> None:
        """Test get_by_id returns student when it exists."""
        result = await student_repository.get_by_id(fixed_student_id)

        assert result is not None
        assert result.id == fixed_student_id
        assert result.first_name == "John"

    async def test_returns_none_when_not_found(
        self,
        student_repository: PostgresStudentRepository,
    ) -> None:
        """Test get_by_id returns None when student doesn't exist."""
        non_existent_id = StudentId(value=UUID("99999999-9999-9999-9999-999999999999"))

        result = await student_repository.get_by_id(non_existent_id)

        assert result is None

    async def test_returns_correct_entity_fields(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        fixed_student_id: StudentId,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get_by_id returns entity with all fields correctly mapped."""
        result = await student_repository.get_by_id(fixed_student_id)

        assert result is not None
        assert isinstance(result, Student)
        assert result.school_id == fixed_school_id
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        assert result.email == "john.doe@example.com"
        assert result.status == StudentStatus.ACTIVE


# ============================================================================
# save Tests
# ============================================================================


class TestPostgresStudentRepositorySave:
    """Tests for save method."""

    async def test_save_inserts_new_student(
        self,
        student_repository: PostgresStudentRepository,
        sample_student: Student,
        saved_school: SchoolModel,
    ) -> None:
        """Test save inserts new student into database."""
        result = await student_repository.save(sample_student)

        assert result.id == sample_student.id
        assert result.first_name == sample_student.first_name

        # Verify it was persisted
        fetched = await student_repository.get_by_id(sample_student.id)
        assert fetched is not None

    async def test_save_updates_existing_student(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        fixed_student_id: StudentId,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
    ) -> None:
        """Test save updates existing student."""
        updated_student = Student(
            id=fixed_student_id,
            school_id=fixed_school_id,
            first_name="John",
            last_name="Updated",
            email="john.updated@example.com",
            enrollment_date=fixed_time,
            status=StudentStatus.GRADUATED,
            created_at=fixed_time,
            updated_at=fixed_time,
        )

        result = await student_repository.save(updated_student)

        assert result.last_name == "Updated"
        assert result.status == StudentStatus.GRADUATED


# ============================================================================
# exists_by_email Tests
# ============================================================================


class TestPostgresStudentRepositoryExistsByEmail:
    """Tests for exists_by_email method."""

    async def test_returns_true_when_email_exists(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
    ) -> None:
        """Test exists_by_email returns True when email exists."""
        result = await student_repository.exists_by_email("john.doe@example.com")

        assert result is True

    async def test_returns_false_when_email_not_exists(
        self,
        student_repository: PostgresStudentRepository,
    ) -> None:
        """Test exists_by_email returns False when email doesn't exist."""
        result = await student_repository.exists_by_email("nonexistent@example.com")

        assert result is False


# ============================================================================
# count_by_school Tests
# ============================================================================


class TestPostgresStudentRepositoryCountBySchool:
    """Tests for count_by_school method."""

    async def test_returns_correct_count(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
        saved_student_3: StudentModel,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test count_by_school returns correct count for school."""
        result = await student_repository.count_by_school(fixed_school_id)

        assert result == 2

    async def test_returns_zero_for_empty_school(
        self,
        student_repository: PostgresStudentRepository,
        saved_school: SchoolModel,
    ) -> None:
        """Test count_by_school returns 0 for school with no students."""
        empty_school_id = SchoolId(value=saved_school.id)

        result = await student_repository.count_by_school(empty_school_id)

        assert result == 0


# ============================================================================
# find Tests - Filtering
# ============================================================================


class TestPostgresStudentRepositoryFind:
    """Tests for find method."""

    async def test_find_returns_all_students_without_filters(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
        saved_student_3: StudentModel,
    ) -> None:
        """Test find returns all students when no filters applied."""
        result = await student_repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 3

    async def test_find_filters_by_school_id(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
        saved_student_3: StudentModel,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test find filters by school_id correctly."""
        result = await student_repository.find(
            filters=StudentFilters(school_id=fixed_school_id.value),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 2
        for student in result.items:
            assert student.school_id == fixed_school_id

    async def test_find_filters_by_status(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
        saved_student_3: StudentModel,
    ) -> None:
        """Test find filters by status correctly."""
        result = await student_repository.find(
            filters=StudentFilters(status="active"),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert result.items[0].status == StudentStatus.ACTIVE

    async def test_find_filters_by_email(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
    ) -> None:
        """Test find filters by email correctly."""
        result = await student_repository.find(
            filters=StudentFilters(email="john.doe@example.com"),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert result.items[0].email == "john.doe@example.com"


# ============================================================================
# find Tests - Pagination
# ============================================================================


class TestPostgresStudentRepositoryFindPagination:
    """Tests for find method pagination."""

    async def test_find_respects_offset(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
        saved_student_3: StudentModel,
    ) -> None:
        """Test find respects pagination offset."""
        result = await student_repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=1, limit=10),
            sort=SortParams(sort_by="first_name", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.offset == 1

    async def test_find_respects_limit(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
        saved_student_3: StudentModel,
    ) -> None:
        """Test find respects pagination limit."""
        result = await student_repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=2),
            sort=SortParams(sort_by="first_name", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.limit == 2

    async def test_find_returns_correct_total(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
        saved_student_3: StudentModel,
    ) -> None:
        """Test find returns correct total count regardless of pagination."""
        result = await student_repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=1),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 1


# ============================================================================
# find Tests - Sorting
# ============================================================================


class TestPostgresStudentRepositoryFindSorting:
    """Tests for find method sorting."""

    async def test_find_sorts_by_first_name_ascending(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
        saved_student_3: StudentModel,
    ) -> None:
        """Test find sorts by first_name ascending."""
        result = await student_repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="first_name", sort_order="asc"),
        )

        names = [s.first_name for s in result.items]
        assert names == ["Bob", "Jane", "John"]

    async def test_find_sorts_by_enrollment_date_descending(
        self,
        student_repository: PostgresStudentRepository,
        saved_student: StudentModel,
        saved_student_2: StudentModel,
        saved_student_3: StudentModel,
    ) -> None:
        """Test find sorts by enrollment_date descending."""
        result = await student_repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="enrollment_date", sort_order="desc"),
        )

        dates = [s.enrollment_date for s in result.items]
        assert dates == sorted(dates, reverse=True)
