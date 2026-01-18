"""Integration tests for PostgresSchoolRepository.

These tests verify the PostgreSQL repository implementation against
a real database. They test SQL query correctness and database interactions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import SchoolFilters
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.infrastructure.adapters.school_repository import (
    PostgresSchoolRepository,
)
from mattilda_challenge.infrastructure.postgres.models import SchoolModel

pytestmark = pytest.mark.integration


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def school_repository(db_session: AsyncSession) -> PostgresSchoolRepository:
    """Provide PostgresSchoolRepository instance."""
    return PostgresSchoolRepository(db_session)


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
def fixed_school_id_3() -> SchoolId:
    """Provide third fixed school ID for testing."""
    return SchoolId(value=UUID("33333333-3333-3333-3333-333333333333"))


@pytest.fixture
async def saved_school(
    db_session: AsyncSession,
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> SchoolModel:
    """Insert a school into the test database."""
    school = SchoolModel(
        id=fixed_school_id.value,
        name="Alpha Academy",
        address="123 Education Lane",
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
        name="Beta School",
        address="456 Learning Street",
        created_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
    )
    db_session.add(school)
    await db_session.flush()
    return school


@pytest.fixture
async def saved_school_3(
    db_session: AsyncSession,
    fixed_school_id_3: SchoolId,
) -> SchoolModel:
    """Insert third school into the test database."""
    school = SchoolModel(
        id=fixed_school_id_3.value,
        name="Gamma Institute",
        address="789 Knowledge Ave",
        created_at=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
    )
    db_session.add(school)
    await db_session.flush()
    return school


@pytest.fixture
def sample_school(
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> School:
    """Create a sample School domain entity."""
    return School(
        id=fixed_school_id,
        name="Alpha Academy",
        address="123 Education Lane",
        created_at=fixed_time,
    )


# ============================================================================
# get_by_id Tests
# ============================================================================


class TestPostgresSchoolRepositoryGetById:
    """Tests for get_by_id method."""

    async def test_returns_school_when_exists(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get_by_id returns school when it exists."""
        result = await school_repository.get_by_id(fixed_school_id)

        assert result is not None
        assert result.id == fixed_school_id
        assert result.name == "Alpha Academy"

    async def test_returns_none_when_not_found(
        self,
        school_repository: PostgresSchoolRepository,
    ) -> None:
        """Test get_by_id returns None when school doesn't exist."""
        non_existent_id = SchoolId(value=UUID("99999999-9999-9999-9999-999999999999"))

        result = await school_repository.get_by_id(non_existent_id)

        assert result is None

    async def test_returns_correct_entity_fields(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get_by_id returns entity with all fields correctly mapped."""
        result = await school_repository.get_by_id(fixed_school_id)

        assert result is not None
        assert isinstance(result, School)
        assert result.name == "Alpha Academy"
        assert result.address == "123 Education Lane"

    async def test_for_update_parameter_accepted(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get_by_id accepts for_update parameter."""
        result = await school_repository.get_by_id(fixed_school_id, for_update=True)

        assert result is not None
        assert result.id == fixed_school_id


# ============================================================================
# save Tests
# ============================================================================


class TestPostgresSchoolRepositorySave:
    """Tests for save method."""

    async def test_save_inserts_new_school(
        self,
        school_repository: PostgresSchoolRepository,
        sample_school: School,
    ) -> None:
        """Test save inserts new school into database."""
        result = await school_repository.save(sample_school)

        assert result.id == sample_school.id
        assert result.name == sample_school.name

        # Verify it was persisted
        fetched = await school_repository.get_by_id(sample_school.id)
        assert fetched is not None
        assert fetched.id == sample_school.id

    async def test_save_updates_existing_school(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
    ) -> None:
        """Test save updates existing school."""
        updated_school = School(
            id=fixed_school_id,
            name="Updated Academy",
            address="999 New Street",
            created_at=fixed_time,
        )

        result = await school_repository.save(updated_school)

        assert result.name == "Updated Academy"
        assert result.address == "999 New Street"


# ============================================================================
# find Tests - Filtering
# ============================================================================


class TestPostgresSchoolRepositoryFind:
    """Tests for find method."""

    async def test_find_returns_all_schools_without_filters(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        saved_school_2: SchoolModel,
        saved_school_3: SchoolModel,
    ) -> None:
        """Test find returns all schools when no filters applied."""
        result = await school_repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 3

    async def test_find_filters_by_name_partial_match(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        saved_school_2: SchoolModel,
        saved_school_3: SchoolModel,
    ) -> None:
        """Test find filters by name with partial case-insensitive match."""
        result = await school_repository.find(
            filters=SchoolFilters(name="academy"),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert result.items[0].name == "Alpha Academy"


# ============================================================================
# find Tests - Pagination
# ============================================================================


class TestPostgresSchoolRepositoryFindPagination:
    """Tests for find method pagination."""

    async def test_find_respects_offset(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        saved_school_2: SchoolModel,
        saved_school_3: SchoolModel,
    ) -> None:
        """Test find respects pagination offset."""
        result = await school_repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=1, limit=10),
            sort=SortParams(sort_by="name", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.offset == 1

    async def test_find_respects_limit(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        saved_school_2: SchoolModel,
        saved_school_3: SchoolModel,
    ) -> None:
        """Test find respects pagination limit."""
        result = await school_repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=2),
            sort=SortParams(sort_by="name", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.limit == 2

    async def test_find_returns_correct_total(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        saved_school_2: SchoolModel,
        saved_school_3: SchoolModel,
    ) -> None:
        """Test find returns correct total count regardless of pagination."""
        result = await school_repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=1),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 1


# ============================================================================
# find Tests - Sorting
# ============================================================================


class TestPostgresSchoolRepositoryFindSorting:
    """Tests for find method sorting."""

    async def test_find_sorts_by_name_ascending(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        saved_school_2: SchoolModel,
        saved_school_3: SchoolModel,
    ) -> None:
        """Test find sorts by name ascending."""
        result = await school_repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="name", sort_order="asc"),
        )

        names = [s.name for s in result.items]
        assert names == ["Alpha Academy", "Beta School", "Gamma Institute"]

    async def test_find_sorts_by_created_at_descending(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
        saved_school_2: SchoolModel,
        saved_school_3: SchoolModel,
    ) -> None:
        """Test find sorts by created_at descending."""
        result = await school_repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        dates = [s.created_at for s in result.items]
        assert dates == sorted(dates, reverse=True)

    async def test_find_returns_page_object(
        self,
        school_repository: PostgresSchoolRepository,
        saved_school: SchoolModel,
    ) -> None:
        """Test find returns Page object with correct structure."""
        result = await school_repository.find(
            filters=SchoolFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert isinstance(result, Page)
        assert isinstance(result.items, tuple)
        assert result.offset == 0
        assert result.limit == 10
