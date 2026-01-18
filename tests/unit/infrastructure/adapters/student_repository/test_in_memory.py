"""Unit tests for InMemoryStudentRepository.

These tests verify the in-memory repository implementation used for
unit testing use cases. While this is test infrastructure, it contains
non-trivial logic (filtering, sorting, pagination) that could have bugs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import StudentFilters
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId, StudentStatus
from mattilda_challenge.infrastructure.adapters.student_repository import (
    InMemoryStudentRepository,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def repository() -> InMemoryStudentRepository:
    """Provide fresh in-memory repository for each test."""
    return InMemoryStudentRepository()


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def school_id_1() -> SchoolId:
    """Provide first school ID for testing."""
    return SchoolId(value=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))


@pytest.fixture
def school_id_2() -> SchoolId:
    """Provide second school ID for testing."""
    return SchoolId(value=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))


@pytest.fixture
def student_1(school_id_1: SchoolId, fixed_time: datetime) -> Student:
    """Create first test student."""
    return Student(
        id=StudentId(value=UUID("11111111-1111-1111-1111-111111111111")),
        school_id=school_id_1,
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        enrollment_date=fixed_time,
        status=StudentStatus.ACTIVE,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def student_2(school_id_1: SchoolId, fixed_time: datetime) -> Student:
    """Create second test student (same school)."""
    return Student(
        id=StudentId(value=UUID("22222222-2222-2222-2222-222222222222")),
        school_id=school_id_1,
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
        enrollment_date=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
        status=StudentStatus.INACTIVE,
        created_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def student_3(school_id_2: SchoolId, fixed_time: datetime) -> Student:
    """Create third test student (different school)."""
    return Student(
        id=StudentId(value=UUID("33333333-3333-3333-3333-333333333333")),
        school_id=school_id_2,
        first_name="Bob",
        last_name="Johnson",
        email="bob.johnson@example.com",
        enrollment_date=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
        status=StudentStatus.GRADUATED,
        created_at=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
        updated_at=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
    )


# ============================================================================
# Basic Operations
# ============================================================================


class TestInMemoryStudentRepositorySave:
    """Tests for save method."""

    async def test_save_stores_student(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
    ) -> None:
        """Test save stores student in repository."""
        result = await repository.save(student_1)

        assert result == student_1
        assert await repository.get_by_id(student_1.id) == student_1

    async def test_save_returns_same_student(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
    ) -> None:
        """Test save returns the saved student."""
        result = await repository.save(student_1)

        assert result is student_1

    async def test_save_overwrites_existing(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        school_id_1: SchoolId,
        fixed_time: datetime,
    ) -> None:
        """Test save overwrites existing student with same ID."""
        await repository.save(student_1)

        updated_student = Student(
            id=student_1.id,
            school_id=school_id_1,
            first_name="John",
            last_name="Updated",
            email="john.updated@example.com",
            enrollment_date=fixed_time,
            status=StudentStatus.GRADUATED,
            created_at=fixed_time,
            updated_at=fixed_time,
        )

        await repository.save(updated_student)
        fetched = await repository.get_by_id(student_1.id)

        assert fetched is not None
        assert fetched.last_name == "Updated"
        assert fetched.status == StudentStatus.GRADUATED


class TestInMemoryStudentRepositoryGetById:
    """Tests for get_by_id method."""

    async def test_get_by_id_returns_student(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
    ) -> None:
        """Test get_by_id returns stored student."""
        await repository.save(student_1)

        result = await repository.get_by_id(student_1.id)

        assert result == student_1

    async def test_get_by_id_returns_none_when_not_found(
        self,
        repository: InMemoryStudentRepository,
    ) -> None:
        """Test get_by_id returns None for non-existent ID."""
        non_existent_id = StudentId(value=UUID("99999999-9999-9999-9999-999999999999"))

        result = await repository.get_by_id(non_existent_id)

        assert result is None

    async def test_get_by_id_accepts_for_update_parameter(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
    ) -> None:
        """Test get_by_id accepts for_update parameter (ignored in memory)."""
        await repository.save(student_1)

        result = await repository.get_by_id(student_1.id, for_update=True)

        assert result == student_1


# ============================================================================
# Special Methods
# ============================================================================


class TestInMemoryStudentRepositoryExistsByEmail:
    """Tests for exists_by_email method."""

    async def test_exists_by_email_returns_true_when_exists(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
    ) -> None:
        """Test exists_by_email returns True when email exists."""
        repository.add(student_1)

        result = await repository.exists_by_email("john.doe@example.com")

        assert result is True

    async def test_exists_by_email_returns_false_when_not_exists(
        self,
        repository: InMemoryStudentRepository,
    ) -> None:
        """Test exists_by_email returns False when email not found."""
        result = await repository.exists_by_email("nonexistent@example.com")

        assert result is False

    async def test_exists_by_email_is_case_sensitive(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
    ) -> None:
        """Test exists_by_email is case sensitive (as stored)."""
        repository.add(student_1)

        # Exact match should work
        assert await repository.exists_by_email("john.doe@example.com") is True
        # Different case should not match (matches domain behavior)
        assert await repository.exists_by_email("JOHN.DOE@EXAMPLE.COM") is False


class TestInMemoryStudentRepositoryCountBySchool:
    """Tests for count_by_school method."""

    async def test_count_by_school_returns_correct_count(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
        school_id_1: SchoolId,
    ) -> None:
        """Test count_by_school returns correct count for school."""
        repository.add(student_1)  # school_id_1
        repository.add(student_2)  # school_id_1
        repository.add(student_3)  # school_id_2

        result = await repository.count_by_school(school_id_1)

        assert result == 2

    async def test_count_by_school_returns_zero_for_empty_school(
        self,
        repository: InMemoryStudentRepository,
    ) -> None:
        """Test count_by_school returns 0 for school with no students."""
        empty_school_id = SchoolId(value=UUID("88888888-8888-8888-8888-888888888888"))

        result = await repository.count_by_school(empty_school_id)

        assert result == 0


# ============================================================================
# Filtering
# ============================================================================


class TestInMemoryStudentRepositoryFindFilters:
    """Tests for find method filtering."""

    async def test_find_returns_all_without_filters(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
    ) -> None:
        """Test find returns all students when no filters applied."""
        repository.add(student_1)
        repository.add(student_2)
        repository.add(student_3)

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 3

    async def test_find_filters_by_school_id(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
        school_id_1: SchoolId,
    ) -> None:
        """Test find filters by school_id correctly."""
        repository.add(student_1)
        repository.add(student_2)
        repository.add(student_3)

        result = await repository.find(
            filters=StudentFilters(school_id=school_id_1.value),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 2
        for student in result.items:
            assert student.school_id == school_id_1

    async def test_find_filters_by_status(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
    ) -> None:
        """Test find filters by status correctly."""
        repository.add(student_1)  # active
        repository.add(student_2)  # inactive
        repository.add(student_3)  # graduated

        result = await repository.find(
            filters=StudentFilters(status="active"),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert result.items[0].status == StudentStatus.ACTIVE

    async def test_find_filters_by_email(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
    ) -> None:
        """Test find filters by email correctly."""
        repository.add(student_1)
        repository.add(student_2)

        result = await repository.find(
            filters=StudentFilters(email="john.doe@example.com"),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert result.items[0].email == "john.doe@example.com"

    async def test_find_multiple_filters_combined(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
        school_id_1: SchoolId,
    ) -> None:
        """Test find combines multiple filters with AND logic."""
        repository.add(student_1)  # school_id_1, active
        repository.add(student_2)  # school_id_1, inactive
        repository.add(student_3)  # school_id_2, graduated

        result = await repository.find(
            filters=StudentFilters(
                school_id=school_id_1.value,
                status="active",
            ),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert result.items[0].id == student_1.id


# ============================================================================
# Sorting
# ============================================================================


class TestInMemoryStudentRepositoryFindSorting:
    """Tests for find method sorting."""

    async def test_find_sorts_by_first_name_ascending(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
    ) -> None:
        """Test find sorts by first_name ascending."""
        repository.add(student_1)  # John
        repository.add(student_2)  # Jane
        repository.add(student_3)  # Bob

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="first_name", sort_order="asc"),
        )

        names = [s.first_name for s in result.items]
        assert names == ["Bob", "Jane", "John"]

    async def test_find_sorts_by_last_name_descending(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
    ) -> None:
        """Test find sorts by last_name descending."""
        repository.add(student_1)  # Doe
        repository.add(student_2)  # Smith
        repository.add(student_3)  # Johnson

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="last_name", sort_order="desc"),
        )

        names = [s.last_name for s in result.items]
        assert names == ["Smith", "Johnson", "Doe"]

    async def test_find_sorts_by_enrollment_date_ascending(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
    ) -> None:
        """Test find sorts by enrollment_date ascending."""
        repository.add(student_1)  # 2024-01-15
        repository.add(student_2)  # 2024-01-16
        repository.add(student_3)  # 2024-01-17

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="enrollment_date", sort_order="asc"),
        )

        dates = [s.enrollment_date for s in result.items]
        assert dates == sorted(dates)

    async def test_find_sorts_by_status(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
    ) -> None:
        """Test find sorts by status."""
        repository.add(student_1)  # active
        repository.add(student_2)  # inactive
        repository.add(student_3)  # graduated

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="status", sort_order="asc"),
        )

        statuses = [s.status.value for s in result.items]
        assert statuses == sorted(statuses)


# ============================================================================
# Pagination
# ============================================================================


class TestInMemoryStudentRepositoryFindPagination:
    """Tests for find method pagination."""

    async def test_find_respects_offset(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
    ) -> None:
        """Test find respects pagination offset."""
        repository.add(student_1)
        repository.add(student_2)
        repository.add(student_3)

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=1, limit=10),
            sort=SortParams(sort_by="first_name", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.offset == 1

    async def test_find_respects_limit(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
    ) -> None:
        """Test find respects pagination limit."""
        repository.add(student_1)
        repository.add(student_2)
        repository.add(student_3)

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=2),
            sort=SortParams(sort_by="first_name", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.limit == 2

    async def test_find_returns_correct_total(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
        student_3: Student,
    ) -> None:
        """Test find returns correct total count regardless of pagination."""
        repository.add(student_1)
        repository.add(student_2)
        repository.add(student_3)

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=1),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 1

    async def test_find_returns_page_object(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
    ) -> None:
        """Test find returns Page object with correct structure."""
        repository.add(student_1)

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert isinstance(result, Page)
        assert isinstance(result.items, tuple)
        assert result.offset == 0
        assert result.limit == 10


# ============================================================================
# Test Helper Methods
# ============================================================================


class TestInMemoryStudentRepositoryHelpers:
    """Tests for test helper methods."""

    async def test_add_stores_student_directly(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
    ) -> None:
        """Test add() stores student without async."""
        repository.add(student_1)

        result = await repository.get_by_id(student_1.id)

        assert result == student_1

    async def test_clear_removes_all_students(
        self,
        repository: InMemoryStudentRepository,
        student_1: Student,
        student_2: Student,
    ) -> None:
        """Test clear() removes all stored students."""
        repository.add(student_1)
        repository.add(student_2)

        repository.clear()

        assert await repository.get_by_id(student_1.id) is None
        assert await repository.get_by_id(student_2.id) is None

        result = await repository.find(
            filters=StudentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )
        assert result.total == 0
