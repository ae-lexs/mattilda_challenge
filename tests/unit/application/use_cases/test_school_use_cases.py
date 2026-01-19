"""Unit tests for School use cases.

Tests for CreateSchoolUseCase, UpdateSchoolUseCase, DeleteSchoolUseCase,
and ListSchoolsUseCase following the Arrange-Act-Assert pattern.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from mattilda_challenge.application.common import PaginationParams, SortParams
from mattilda_challenge.application.filters import SchoolFilters
from mattilda_challenge.application.use_cases import (
    CreateSchoolUseCase,
    DeleteSchoolUseCase,
    ListSchoolsUseCase,
    UpdateSchoolUseCase,
)
from mattilda_challenge.application.use_cases.requests import (
    CreateSchoolRequest,
    DeleteSchoolRequest,
    UpdateSchoolRequest,
)
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.exceptions import SchoolNotFoundError
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.infrastructure.adapters import InMemoryUnitOfWork

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_school_id() -> SchoolId:
    """Provide fixed school ID for testing."""
    return SchoolId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def sample_school(fixed_school_id: SchoolId, fixed_time: datetime) -> School:
    """Provide sample school entity for testing."""
    return School(
        id=fixed_school_id,
        name="Test School",
        address="123 Test Street",
        created_at=fixed_time,
    )


@pytest.fixture
def uow() -> InMemoryUnitOfWork:
    """Provide fresh InMemoryUnitOfWork for each test."""
    return InMemoryUnitOfWork()


# ============================================================================
# CreateSchoolUseCase
# ============================================================================


class TestCreateSchoolUseCase:
    """Tests for CreateSchoolUseCase."""

    async def test_execute_creates_school_with_correct_name(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates school with the provided name."""
        # Arrange
        use_case = CreateSchoolUseCase()
        request = CreateSchoolRequest(
            name="New School",
            address="456 New Street",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.name == "New School"

    async def test_execute_creates_school_with_correct_address(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates school with the provided address."""
        # Arrange
        use_case = CreateSchoolUseCase()
        request = CreateSchoolRequest(
            name="New School",
            address="456 New Street",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.address == "456 New Street"

    async def test_execute_creates_school_with_correct_timestamp(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates school with the injected timestamp."""
        # Arrange
        use_case = CreateSchoolUseCase()
        request = CreateSchoolRequest(
            name="New School",
            address="456 New Street",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.created_at == fixed_time

    async def test_execute_persists_school_to_repository(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute persists school to repository."""
        # Arrange
        use_case = CreateSchoolUseCase()
        request = CreateSchoolRequest(
            name="New School",
            address="456 New Street",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        saved = await uow.schools.get_by_id(result.id)
        assert saved is not None
        assert saved.name == "New School"

    async def test_execute_commits_transaction(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute commits the transaction."""
        # Arrange
        use_case = CreateSchoolUseCase()
        request = CreateSchoolRequest(
            name="New School",
            address="456 New Street",
        )

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        assert uow.committed is True

    async def test_execute_strips_whitespace_from_name(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute strips whitespace from name."""
        # Arrange
        use_case = CreateSchoolUseCase()
        request = CreateSchoolRequest(
            name="  New School  ",
            address="456 New Street",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.name == "New School"


# ============================================================================
# UpdateSchoolUseCase
# ============================================================================


class TestUpdateSchoolUseCase:
    """Tests for UpdateSchoolUseCase."""

    async def test_execute_updates_school_name(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute updates school name when provided."""
        # Arrange
        await uow.schools.save(sample_school)
        uow.reset_tracking()
        use_case = UpdateSchoolUseCase()
        request = UpdateSchoolRequest(
            school_id=sample_school.id,
            name="Updated Name",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.name == "Updated Name"

    async def test_execute_updates_school_address(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute updates school address when provided."""
        # Arrange
        await uow.schools.save(sample_school)
        uow.reset_tracking()
        use_case = UpdateSchoolUseCase()
        request = UpdateSchoolRequest(
            school_id=sample_school.id,
            address="Updated Address",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.address == "Updated Address"

    async def test_execute_preserves_unchanged_fields(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute preserves fields not included in update."""
        # Arrange
        await uow.schools.save(sample_school)
        uow.reset_tracking()
        use_case = UpdateSchoolUseCase()
        request = UpdateSchoolRequest(
            school_id=sample_school.id,
            name="Updated Name",
            # address not provided
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.address == sample_school.address

    async def test_execute_commits_transaction(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute commits the transaction."""
        # Arrange
        await uow.schools.save(sample_school)
        uow.reset_tracking()
        use_case = UpdateSchoolUseCase()
        request = UpdateSchoolRequest(
            school_id=sample_school.id,
            name="Updated Name",
        )

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        assert uow.committed is True

    async def test_execute_raises_when_school_not_found(
        self,
        uow: InMemoryUnitOfWork,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises SchoolNotFoundError when school doesn't exist."""
        # Arrange
        use_case = UpdateSchoolUseCase()
        request = UpdateSchoolRequest(
            school_id=fixed_school_id,
            name="Updated Name",
        )

        # Act & Assert
        with pytest.raises(SchoolNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_school_id.value) in str(exc_info.value)


# ============================================================================
# DeleteSchoolUseCase
# ============================================================================


class TestDeleteSchoolUseCase:
    """Tests for DeleteSchoolUseCase."""

    async def test_execute_raises_when_school_not_found(
        self,
        uow: InMemoryUnitOfWork,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises SchoolNotFoundError when school doesn't exist."""
        # Arrange
        use_case = DeleteSchoolUseCase()
        request = DeleteSchoolRequest(school_id=fixed_school_id)

        # Act & Assert
        with pytest.raises(SchoolNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_school_id.value) in str(exc_info.value)

    async def test_execute_raises_when_school_has_students(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises error when school has enrolled students."""
        # Arrange
        from mattilda_challenge.domain.entities import Student

        await uow.schools.save(sample_school)
        student = Student.create(
            school_id=sample_school.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            now=fixed_time,
        )
        await uow.students.save(student)
        uow.reset_tracking()

        use_case = DeleteSchoolUseCase()
        request = DeleteSchoolRequest(school_id=sample_school.id)

        # Act & Assert
        with pytest.raises(SchoolNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert "enrolled students" in str(exc_info.value)

    async def test_execute_commits_when_school_exists_without_students(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute commits when school exists and has no students."""
        # Arrange
        await uow.schools.save(sample_school)
        uow.reset_tracking()
        use_case = DeleteSchoolUseCase()
        request = DeleteSchoolRequest(school_id=sample_school.id)

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        assert uow.committed is True


# ============================================================================
# ListSchoolsUseCase
# ============================================================================


class TestListSchoolsUseCase:
    """Tests for ListSchoolsUseCase."""

    async def test_execute_returns_empty_page_when_no_schools(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns empty page when no schools exist."""
        # Arrange
        use_case = ListSchoolsUseCase()
        filters = SchoolFilters()
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 0
        assert len(result.items) == 0

    async def test_execute_returns_all_schools(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns all schools when no filters applied."""
        # Arrange
        school1 = School(
            id=SchoolId(value=UUID("11111111-1111-1111-1111-111111111111")),
            name="School A",
            address="Address A",
            created_at=fixed_time,
        )
        school2 = School(
            id=SchoolId(value=UUID("22222222-2222-2222-2222-222222222222")),
            name="School B",
            address="Address B",
            created_at=fixed_time,
        )
        await uow.schools.save(school1)
        await uow.schools.save(school2)

        use_case = ListSchoolsUseCase()
        filters = SchoolFilters()
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 2
        assert len(result.items) == 2

    async def test_execute_applies_pagination(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute applies pagination correctly."""
        # Arrange
        for i in range(5):
            school = School(
                id=SchoolId.generate(),
                name=f"School {i}",
                address=f"Address {i}",
                created_at=fixed_time,
            )
            await uow.schools.save(school)

        use_case = ListSchoolsUseCase()
        filters = SchoolFilters()
        pagination = PaginationParams(offset=0, limit=2)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 5
        assert len(result.items) == 2

    async def test_execute_applies_name_filter(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute filters schools by name."""
        # Arrange
        school1 = School(
            id=SchoolId(value=UUID("11111111-1111-1111-1111-111111111111")),
            name="Alpha School",
            address="Address A",
            created_at=fixed_time,
        )
        school2 = School(
            id=SchoolId(value=UUID("22222222-2222-2222-2222-222222222222")),
            name="Beta Academy",
            address="Address B",
            created_at=fixed_time,
        )
        await uow.schools.save(school1)
        await uow.schools.save(school2)

        use_case = ListSchoolsUseCase()
        filters = SchoolFilters(name="Alpha")
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 1
        assert result.items[0].name == "Alpha School"
