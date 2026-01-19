"""Unit tests for Student use cases.

Tests for CreateStudentUseCase, UpdateStudentUseCase, DeleteStudentUseCase,
and ListStudentsUseCase following the Arrange-Act-Assert pattern.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from mattilda_challenge.application.common import PaginationParams, SortParams
from mattilda_challenge.application.filters import StudentFilters
from mattilda_challenge.application.use_cases import (
    CreateStudentUseCase,
    DeleteStudentUseCase,
    ListStudentsUseCase,
    UpdateStudentUseCase,
)
from mattilda_challenge.application.use_cases.requests import (
    CreateStudentRequest,
    DeleteStudentRequest,
    UpdateStudentRequest,
)
from mattilda_challenge.domain.entities import School, Student
from mattilda_challenge.domain.exceptions import (
    InvalidStudentDataError,
    SchoolNotFoundError,
    StudentNotFoundError,
)
from mattilda_challenge.domain.value_objects import SchoolId, StudentId, StudentStatus
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
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("22222222-2222-2222-2222-222222222222"))


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
def sample_student(
    fixed_student_id: StudentId,
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> Student:
    """Provide sample student entity for testing."""
    return Student(
        id=fixed_student_id,
        school_id=fixed_school_id,
        first_name="John",
        last_name="Doe",
        email="john.doe@test.com",
        enrollment_date=fixed_time,
        status=StudentStatus.ACTIVE,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def uow() -> InMemoryUnitOfWork:
    """Provide fresh InMemoryUnitOfWork for each test."""
    return InMemoryUnitOfWork()


# ============================================================================
# CreateStudentUseCase
# ============================================================================


class TestCreateStudentUseCase:
    """Tests for CreateStudentUseCase."""

    async def test_execute_creates_student_with_correct_name(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates student with the provided names."""
        # Arrange
        await uow.schools.save(sample_school)
        uow.reset_tracking()
        use_case = CreateStudentUseCase()
        request = CreateStudentRequest(
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.first_name == "Jane"
        assert result.last_name == "Smith"

    async def test_execute_creates_student_with_normalized_email(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute normalizes email to lowercase."""
        # Arrange
        await uow.schools.save(sample_school)
        uow.reset_tracking()
        use_case = CreateStudentUseCase()
        request = CreateStudentRequest(
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="Jane.Smith@TEST.com",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.email == "jane.smith@test.com"

    async def test_execute_creates_student_with_active_status(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates student with ACTIVE status by default."""
        # Arrange
        await uow.schools.save(sample_school)
        uow.reset_tracking()
        use_case = CreateStudentUseCase()
        request = CreateStudentRequest(
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.status == StudentStatus.ACTIVE

    async def test_execute_persists_student_to_repository(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute persists student to repository."""
        # Arrange
        await uow.schools.save(sample_school)
        uow.reset_tracking()
        use_case = CreateStudentUseCase()
        request = CreateStudentRequest(
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        saved = await uow.students.get_by_id(result.id)
        assert saved is not None
        assert saved.email == "jane.smith@test.com"

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
        use_case = CreateStudentUseCase()
        request = CreateStudentRequest(
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
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
        use_case = CreateStudentUseCase()
        request = CreateStudentRequest(
            school_id=fixed_school_id,
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@test.com",
        )

        # Act & Assert
        with pytest.raises(SchoolNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_school_id.value) in str(exc_info.value)

    async def test_execute_raises_when_email_already_exists(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises InvalidStudentDataError when email is in use."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = CreateStudentUseCase()
        request = CreateStudentRequest(
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email=sample_student.email,  # Same email
        )

        # Act & Assert
        with pytest.raises(InvalidStudentDataError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert "already in use" in str(exc_info.value)


# ============================================================================
# UpdateStudentUseCase
# ============================================================================


class TestUpdateStudentUseCase:
    """Tests for UpdateStudentUseCase."""

    async def test_execute_updates_student_first_name(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute updates student first name when provided."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = UpdateStudentUseCase()
        request = UpdateStudentRequest(
            student_id=sample_student.id,
            first_name="Updated",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.first_name == "Updated"

    async def test_execute_updates_student_email(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute updates student email when provided."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = UpdateStudentUseCase()
        request = UpdateStudentRequest(
            student_id=sample_student.id,
            email="new.email@test.com",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.email == "new.email@test.com"

    async def test_execute_updates_student_status(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute updates student status when provided."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = UpdateStudentUseCase()
        request = UpdateStudentRequest(
            student_id=sample_student.id,
            status=StudentStatus.INACTIVE,
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.status == StudentStatus.INACTIVE

    async def test_execute_preserves_unchanged_fields(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute preserves fields not included in update."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = UpdateStudentUseCase()
        request = UpdateStudentRequest(
            student_id=sample_student.id,
            first_name="Updated",
            # last_name not provided
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.last_name == sample_student.last_name

    async def test_execute_updates_updated_at_timestamp(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
    ) -> None:
        """Test execute updates the updated_at timestamp."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = UpdateStudentUseCase()
        new_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        request = UpdateStudentRequest(
            student_id=sample_student.id,
            first_name="Updated",
        )

        # Act
        result = await use_case.execute(uow, request, new_time)

        # Assert
        assert result.updated_at == new_time

    async def test_execute_commits_transaction(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute commits the transaction."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = UpdateStudentUseCase()
        request = UpdateStudentRequest(
            student_id=sample_student.id,
            first_name="Updated",
        )

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        assert uow.committed is True

    async def test_execute_raises_when_student_not_found(
        self,
        uow: InMemoryUnitOfWork,
        fixed_student_id: StudentId,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises StudentNotFoundError when student doesn't exist."""
        # Arrange
        use_case = UpdateStudentUseCase()
        request = UpdateStudentRequest(
            student_id=fixed_student_id,
            first_name="Updated",
        )

        # Act & Assert
        with pytest.raises(StudentNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_student_id.value) in str(exc_info.value)

    async def test_execute_raises_when_new_email_already_exists(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises InvalidStudentDataError when new email is in use."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        # Create another student with a different email
        other_student = Student(
            id=StudentId(value=UUID("33333333-3333-3333-3333-333333333333")),
            school_id=sample_school.id,
            first_name="Other",
            last_name="Student",
            email="other@test.com",
            enrollment_date=fixed_time,
            status=StudentStatus.ACTIVE,
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.students.save(other_student)
        uow.reset_tracking()

        use_case = UpdateStudentUseCase()
        request = UpdateStudentRequest(
            student_id=sample_student.id,
            email="other@test.com",  # Try to use other student's email
        )

        # Act & Assert
        with pytest.raises(InvalidStudentDataError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert "already in use" in str(exc_info.value)


# ============================================================================
# DeleteStudentUseCase
# ============================================================================


class TestDeleteStudentUseCase:
    """Tests for DeleteStudentUseCase."""

    async def test_execute_raises_when_student_not_found(
        self,
        uow: InMemoryUnitOfWork,
        fixed_student_id: StudentId,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises StudentNotFoundError when student doesn't exist."""
        # Arrange
        use_case = DeleteStudentUseCase()
        request = DeleteStudentRequest(student_id=fixed_student_id)

        # Act & Assert
        with pytest.raises(StudentNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_student_id.value) in str(exc_info.value)

    async def test_execute_commits_when_student_exists(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute commits when student exists."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = DeleteStudentUseCase()
        request = DeleteStudentRequest(student_id=sample_student.id)

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        assert uow.committed is True


# ============================================================================
# ListStudentsUseCase
# ============================================================================


class TestListStudentsUseCase:
    """Tests for ListStudentsUseCase."""

    async def test_execute_returns_empty_page_when_no_students(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns empty page when no students exist."""
        # Arrange
        use_case = ListStudentsUseCase()
        filters = StudentFilters()
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 0
        assert len(result.items) == 0

    async def test_execute_returns_all_students(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns all students when no filters applied."""
        # Arrange
        await uow.schools.save(sample_school)
        student1 = Student.create(
            school_id=sample_school.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            now=fixed_time,
        )
        student2 = Student.create(
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            now=fixed_time,
        )
        await uow.students.save(student1)
        await uow.students.save(student2)

        use_case = ListStudentsUseCase()
        filters = StudentFilters()
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 2
        assert len(result.items) == 2

    async def test_execute_applies_school_filter(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute filters students by school_id."""
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

        student1 = Student.create(
            school_id=school1.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            now=fixed_time,
        )
        student2 = Student.create(
            school_id=school2.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            now=fixed_time,
        )
        await uow.students.save(student1)
        await uow.students.save(student2)

        use_case = ListStudentsUseCase()
        filters = StudentFilters(school_id=school1.id.value)
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 1
        assert result.items[0].school_id == school1.id

    async def test_execute_applies_status_filter(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute filters students by status."""
        # Arrange
        await uow.schools.save(sample_school)
        active_student = Student.create(
            school_id=sample_school.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            now=fixed_time,
        )
        inactive_student = Student.create(
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            now=fixed_time,
        ).deactivate(fixed_time)

        await uow.students.save(active_student)
        await uow.students.save(inactive_student)

        use_case = ListStudentsUseCase()
        filters = StudentFilters(status=StudentStatus.ACTIVE.value)
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 1
        assert result.items[0].status == StudentStatus.ACTIVE

    async def test_execute_applies_pagination(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute applies pagination correctly."""
        # Arrange
        await uow.schools.save(sample_school)
        for i in range(5):
            student = Student.create(
                school_id=sample_school.id,
                first_name=f"Student{i}",
                last_name="Test",
                email=f"student{i}@test.com",
                now=fixed_time,
            )
            await uow.students.save(student)

        use_case = ListStudentsUseCase()
        filters = StudentFilters()
        pagination = PaginationParams(offset=0, limit=2)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 5
        assert len(result.items) == 2
