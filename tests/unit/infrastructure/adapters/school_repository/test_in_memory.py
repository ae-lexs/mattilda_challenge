"""Unit tests for InMemorySchoolRepository.

These tests verify the in-memory repository implementation used for
unit testing use cases. While this is test infrastructure, it contains
non-trivial logic (filtering, sorting, pagination) that could have bugs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import SchoolFilters
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.infrastructure.adapters.school_repository import (
    InMemorySchoolRepository,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def repository() -> InMemorySchoolRepository:
    """Provide fresh in-memory repository for each test."""
    return InMemorySchoolRepository()


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def school_1(fixed_time: datetime) -> School:
    """Create first test school."""
    return School(
        id=SchoolId(value=UUID("11111111-1111-1111-1111-111111111111")),
        name="Alpha Academy",
        address="123 Education Lane",
        created_at=fixed_time,
    )


@pytest.fixture
def school_2(fixed_time: datetime) -> School:
    """Create second test school."""
    return School(
        id=SchoolId(value=UUID("22222222-2222-2222-2222-222222222222")),
        name="Beta School",
        address="456 Learning Street",
        created_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def school_3(fixed_time: datetime) -> School:
    """Create third test school."""
    return School(
        id=SchoolId(value=UUID("33333333-3333-3333-3333-333333333333")),
        name="Gamma Institute",
        address="789 Knowledge Ave",
        created_at=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
    )


# ============================================================================
# Basic Operations
# ============================================================================


class TestInMemorySchoolRepositorySave:
    """Tests for save method."""

    async def test_save_stores_school(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
    ) -> None:
        """Test save stores school in repository."""
        result = await repository.save(school_1)

        assert result == school_1
        assert await repository.get_by_id(school_1.id) == school_1

    async def test_save_returns_same_school(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
    ) -> None:
        """Test save returns the saved school."""
        result = await repository.save(school_1)

        assert result is school_1

    async def test_save_overwrites_existing(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        fixed_time: datetime,
    ) -> None:
        """Test save overwrites existing school with same ID."""
        await repository.save(school_1)

        updated_school = School(
            id=school_1.id,
            name="Updated Academy",
            address="999 New Street",
            created_at=fixed_time,
        )

        await repository.save(updated_school)
        fetched = await repository.get_by_id(school_1.id)

        assert fetched is not None
        assert fetched.name == "Updated Academy"
        assert fetched.address == "999 New Street"


class TestInMemorySchoolRepositoryGetById:
    """Tests for get_by_id method."""

    async def test_get_by_id_returns_school(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
    ) -> None:
        """Test get_by_id returns stored school."""
        await repository.save(school_1)

        result = await repository.get_by_id(school_1.id)

        assert result == school_1

    async def test_get_by_id_returns_none_when_not_found(
        self,
        repository: InMemorySchoolRepository,
    ) -> None:
        """Test get_by_id returns None for non-existent ID."""
        non_existent_id = SchoolId(value=UUID("99999999-9999-9999-9999-999999999999"))

        result = await repository.get_by_id(non_existent_id)

        assert result is None

    async def test_get_by_id_accepts_for_update_parameter(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
    ) -> None:
        """Test get_by_id accepts for_update parameter (ignored in memory)."""
        await repository.save(school_1)

        result = await repository.get_by_id(school_1.id, for_update=True)

        assert result == school_1


# ============================================================================
# Filtering
# ============================================================================


class TestInMemorySchoolRepositoryFindFilters:
    """Tests for find method filtering."""

    async def test_find_returns_all_without_filters(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
        school_3: School,
    ) -> None:
        """Test find returns all schools when no filters applied."""
        repository.add(school_1)
        repository.add(school_2)
        repository.add(school_3)

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 3

    async def test_find_filters_by_name_partial_match(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
        school_3: School,
    ) -> None:
        """Test find filters by name with partial case-insensitive match."""
        repository.add(school_1)  # Alpha Academy
        repository.add(school_2)  # Beta School
        repository.add(school_3)  # Gamma Institute

        result = await repository.find(
            filters=SchoolFilters(name="academy"),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert result.items[0].name == "Alpha Academy"

    async def test_find_filters_by_name_case_insensitive(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
    ) -> None:
        """Test find filters by name case-insensitively."""
        repository.add(school_1)  # Alpha Academy

        result = await repository.find(
            filters=SchoolFilters(name="ALPHA"),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert result.items[0].name == "Alpha Academy"


# ============================================================================
# Sorting
# ============================================================================


class TestInMemorySchoolRepositoryFindSorting:
    """Tests for find method sorting."""

    async def test_find_sorts_by_name_ascending(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
        school_3: School,
    ) -> None:
        """Test find sorts by name ascending."""
        repository.add(school_1)  # Alpha Academy
        repository.add(school_2)  # Beta School
        repository.add(school_3)  # Gamma Institute

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="name", sort_order="asc"),
        )

        names = [s.name for s in result.items]
        assert names == ["Alpha Academy", "Beta School", "Gamma Institute"]

    async def test_find_sorts_by_name_descending(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
        school_3: School,
    ) -> None:
        """Test find sorts by name descending."""
        repository.add(school_1)
        repository.add(school_2)
        repository.add(school_3)

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="name", sort_order="desc"),
        )

        names = [s.name for s in result.items]
        assert names == ["Gamma Institute", "Beta School", "Alpha Academy"]

    async def test_find_sorts_by_created_at_ascending(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
        school_3: School,
    ) -> None:
        """Test find sorts by created_at ascending."""
        repository.add(school_1)  # 2024-01-15
        repository.add(school_2)  # 2024-01-16
        repository.add(school_3)  # 2024-01-17

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="asc"),
        )

        dates = [s.created_at for s in result.items]
        assert dates == sorted(dates)

    async def test_find_sorts_by_created_at_descending(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
        school_3: School,
    ) -> None:
        """Test find sorts by created_at descending."""
        repository.add(school_1)
        repository.add(school_2)
        repository.add(school_3)

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        dates = [s.created_at for s in result.items]
        assert dates == sorted(dates, reverse=True)

    async def test_find_defaults_to_created_at_for_unknown_sort(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
    ) -> None:
        """Test find defaults to created_at for unknown sort field."""
        repository.add(school_1)

        # Should not raise, falls back to created_at
        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="unknown_field", sort_order="asc"),
        )

        assert len(result.items) == 1


# ============================================================================
# Pagination
# ============================================================================


class TestInMemorySchoolRepositoryFindPagination:
    """Tests for find method pagination."""

    async def test_find_respects_offset(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
        school_3: School,
    ) -> None:
        """Test find respects pagination offset."""
        repository.add(school_1)
        repository.add(school_2)
        repository.add(school_3)

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=1, limit=10),
            sort=SortParams(sort_by="name", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2  # Skipped first one
        assert result.offset == 1

    async def test_find_respects_limit(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
        school_3: School,
    ) -> None:
        """Test find respects pagination limit."""
        repository.add(school_1)
        repository.add(school_2)
        repository.add(school_3)

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=2),
            sort=SortParams(sort_by="name", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.limit == 2

    async def test_find_returns_correct_total(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
        school_3: School,
    ) -> None:
        """Test find returns correct total count regardless of pagination."""
        repository.add(school_1)
        repository.add(school_2)
        repository.add(school_3)

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=1),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 1

    async def test_find_offset_beyond_results(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
    ) -> None:
        """Test find returns empty when offset exceeds total."""
        repository.add(school_1)

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=10, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert len(result.items) == 0

    async def test_find_returns_page_object(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
    ) -> None:
        """Test find returns Page object with correct structure."""
        repository.add(school_1)

        result = await repository.find(
            filters=SchoolFilters(),
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


class TestInMemorySchoolRepositoryHelpers:
    """Tests for test helper methods."""

    async def test_add_stores_school_directly(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
    ) -> None:
        """Test add() stores school without async."""
        repository.add(school_1)

        result = await repository.get_by_id(school_1.id)

        assert result == school_1

    async def test_clear_removes_all_schools(
        self,
        repository: InMemorySchoolRepository,
        school_1: School,
        school_2: School,
    ) -> None:
        """Test clear() removes all stored schools."""
        repository.add(school_1)
        repository.add(school_2)

        repository.clear()

        assert await repository.get_by_id(school_1.id) is None
        assert await repository.get_by_id(school_2.id) is None

        result = await repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )
        assert result.total == 0
