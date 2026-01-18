"""Tests for Student entity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.entities.student import StudentStatus
from mattilda_challenge.domain.exceptions import InvalidStudentDataError
from mattilda_challenge.domain.value_objects import SchoolId, StudentId


class TestStudentStatus:
    """Tests for StudentStatus enum."""

    def test_status_values(self) -> None:
        """Test that status enum has expected values."""
        assert StudentStatus.ACTIVE.value == "active"
        assert StudentStatus.INACTIVE.value == "inactive"
        assert StudentStatus.GRADUATED.value == "graduated"

    def test_str_returns_value(self) -> None:
        """Test that __str__ returns the enum value."""
        assert str(StudentStatus.ACTIVE) == "active"
        assert str(StudentStatus.INACTIVE) == "inactive"
        assert str(StudentStatus.GRADUATED) == "graduated"


class TestStudentCreation:
    """Tests for Student entity creation."""

    def test_create_with_valid_data(self) -> None:
        """Test creating student with valid data."""
        student_id = StudentId.generate()
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        student = Student(
            id=student_id,
            school_id=school_id,
            first_name="Juan",
            last_name="Pérez",
            email="juan.perez@example.com",
            enrollment_date=now,
            status=StudentStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

        assert student.id == student_id
        assert student.school_id == school_id
        assert student.first_name == "Juan"
        assert student.last_name == "Pérez"
        assert student.email == "juan.perez@example.com"
        assert student.enrollment_date == now
        assert student.status == StudentStatus.ACTIVE
        assert student.created_at == now
        assert student.updated_at == now

    def test_create_factory_method(self) -> None:
        """Test Student.create() factory method."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        student = Student.create(
            school_id=school_id,
            first_name="María",
            last_name="García",
            email="Maria.Garcia@Example.COM",
            now=now,
        )

        assert isinstance(student.id, StudentId)
        assert isinstance(student.id.value, UUID)
        assert student.school_id == school_id
        assert student.first_name == "María"
        assert student.last_name == "García"
        assert student.email == "maria.garcia@example.com"  # Lowercased
        assert student.enrollment_date == now
        assert student.status == StudentStatus.ACTIVE
        assert student.created_at == now
        assert student.updated_at == now

    def test_create_strips_whitespace(self) -> None:
        """Test Student.create() strips leading/trailing whitespace."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        student = Student.create(
            school_id=school_id,
            first_name="  Juan  ",
            last_name="  Pérez  ",
            email="  juan@example.com  ",
            now=now,
        )

        assert student.first_name == "Juan"
        assert student.last_name == "Pérez"
        assert student.email == "juan@example.com"


class TestStudentValidation:
    """Tests for Student entity validation."""

    def test_empty_first_name_raises_error(self) -> None:
        """Test that empty first name raises InvalidStudentDataError."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidStudentDataError) as exc_info:
            Student(
                id=StudentId.generate(),
                school_id=school_id,
                first_name="",
                last_name="Pérez",
                email="juan@example.com",
                enrollment_date=now,
                status=StudentStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )

        assert "First name cannot be empty" in str(exc_info.value)

    def test_whitespace_only_first_name_raises_error(self) -> None:
        """Test that whitespace-only first name raises error."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidStudentDataError) as exc_info:
            Student(
                id=StudentId.generate(),
                school_id=school_id,
                first_name="   ",
                last_name="Pérez",
                email="juan@example.com",
                enrollment_date=now,
                status=StudentStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )

        assert "First name cannot be empty" in str(exc_info.value)

    def test_empty_last_name_raises_error(self) -> None:
        """Test that empty last name raises InvalidStudentDataError."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidStudentDataError) as exc_info:
            Student(
                id=StudentId.generate(),
                school_id=school_id,
                first_name="Juan",
                last_name="",
                email="juan@example.com",
                enrollment_date=now,
                status=StudentStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )

        assert "Last name cannot be empty" in str(exc_info.value)

    def test_invalid_email_without_at_raises_error(self) -> None:
        """Test that email without @ raises error."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidStudentDataError) as exc_info:
            Student(
                id=StudentId.generate(),
                school_id=school_id,
                first_name="Juan",
                last_name="Pérez",
                email="juan.example.com",
                enrollment_date=now,
                status=StudentStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )

        assert "Invalid email format" in str(exc_info.value)

    def test_invalid_email_without_dot_after_at_raises_error(self) -> None:
        """Test that email without dot after @ raises error."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidStudentDataError) as exc_info:
            Student(
                id=StudentId.generate(),
                school_id=school_id,
                first_name="Juan",
                last_name="Pérez",
                email="juan@example",
                enrollment_date=now,
                status=StudentStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )

        assert "Invalid email format" in str(exc_info.value)

    def test_empty_email_raises_error(self) -> None:
        """Test that empty email raises error."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidStudentDataError) as exc_info:
            Student(
                id=StudentId.generate(),
                school_id=school_id,
                first_name="Juan",
                last_name="Pérez",
                email="",
                enrollment_date=now,
                status=StudentStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )

        assert "Invalid email format" in str(exc_info.value)

    def test_naive_enrollment_date_raises_error(self) -> None:
        """Test that naive enrollment_date raises error."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)

        with pytest.raises(InvalidStudentDataError) as exc_info:
            Student(
                id=StudentId.generate(),
                school_id=school_id,
                first_name="Juan",
                last_name="Pérez",
                email="juan@example.com",
                enrollment_date=naive_dt,
                status=StudentStatus.ACTIVE,
                created_at=now,
                updated_at=now,
            )

        assert "Enrollment date must have UTC timezone" in str(exc_info.value)

    def test_non_utc_created_at_raises_error(self) -> None:
        """Test that non-UTC created_at raises error."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)
        eastern = timezone(timedelta(hours=-5))
        non_utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(InvalidStudentDataError) as exc_info:
            Student(
                id=StudentId.generate(),
                school_id=school_id,
                first_name="Juan",
                last_name="Pérez",
                email="juan@example.com",
                enrollment_date=now,
                status=StudentStatus.ACTIVE,
                created_at=non_utc_dt,
                updated_at=now,
            )

        assert "Created timestamp must have UTC timezone" in str(exc_info.value)

    def test_non_utc_updated_at_raises_error(self) -> None:
        """Test that non-UTC updated_at raises error."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)
        eastern = timezone(timedelta(hours=-5))
        non_utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(InvalidStudentDataError) as exc_info:
            Student(
                id=StudentId.generate(),
                school_id=school_id,
                first_name="Juan",
                last_name="Pérez",
                email="juan@example.com",
                enrollment_date=now,
                status=StudentStatus.ACTIVE,
                created_at=now,
                updated_at=non_utc_dt,
            )

        assert "Updated timestamp must have UTC timezone" in str(exc_info.value)


class TestStudentStatusTransitions:
    """Tests for Student status transition methods."""

    def test_deactivate_returns_inactive_student(self) -> None:
        """Test deactivate() returns new student with INACTIVE status."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)
        later = now + timedelta(days=1)

        student = Student.create(
            school_id=school_id,
            first_name="Juan",
            last_name="Pérez",
            email="juan@example.com",
            now=now,
        )

        deactivated = student.deactivate(later)

        # Original unchanged
        assert student.status == StudentStatus.ACTIVE
        assert student.updated_at == now

        # New instance updated
        assert deactivated.status == StudentStatus.INACTIVE
        assert deactivated.updated_at == later

        # Other fields unchanged
        assert deactivated.id == student.id
        assert deactivated.first_name == student.first_name

    def test_graduate_returns_graduated_student(self) -> None:
        """Test graduate() returns new student with GRADUATED status."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)
        later = now + timedelta(days=365)

        student = Student.create(
            school_id=school_id,
            first_name="María",
            last_name="García",
            email="maria@example.com",
            now=now,
        )

        graduated = student.graduate(later)

        # Original unchanged
        assert student.status == StudentStatus.ACTIVE
        assert student.updated_at == now

        # New instance updated
        assert graduated.status == StudentStatus.GRADUATED
        assert graduated.updated_at == later

        # Other fields unchanged
        assert graduated.id == student.id
        assert graduated.first_name == student.first_name


class TestStudentProperties:
    """Tests for Student computed properties."""

    def test_full_name_property(self) -> None:
        """Test full_name returns first and last name combined."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        student = Student.create(
            school_id=school_id,
            first_name="Juan",
            last_name="Pérez",
            email="juan@example.com",
            now=now,
        )

        assert student.full_name == "Juan Pérez"


class TestStudentImmutability:
    """Tests for Student entity immutability."""

    def test_student_is_immutable(self) -> None:
        """Test that Student attributes cannot be modified."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        student = Student.create(
            school_id=school_id,
            first_name="Juan",
            last_name="Pérez",
            email="juan@example.com",
            now=now,
        )

        with pytest.raises(AttributeError):
            student.first_name = "Carlos"  # type: ignore[misc]

    def test_student_is_hashable(self) -> None:
        """Test that Student can be used in sets and as dict keys."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        student = Student.create(
            school_id=school_id,
            first_name="Juan",
            last_name="Pérez",
            email="juan@example.com",
            now=now,
        )

        hash_value = hash(student)
        assert isinstance(hash_value, int)

        student_set = {student}
        assert student in student_set
