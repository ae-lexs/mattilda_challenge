"""Tests for School entity."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID

import pytest

from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.exceptions import InvalidSchoolDataError
from mattilda_challenge.domain.value_objects import SchoolId


class TestSchoolCreation:
    """Tests for School entity creation."""

    def test_create_with_valid_data(self) -> None:
        """Test creating school with valid data."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        school = School(
            id=school_id,
            name="Colegio ABC",
            address="123 Main Street",
            created_at=now,
        )

        assert school.id == school_id
        assert school.name == "Colegio ABC"
        assert school.address == "123 Main Street"
        assert school.created_at == now

    def test_create_factory_method(self) -> None:
        """Test School.create() factory method generates ID and sets timestamp."""
        now = datetime.now(UTC)

        school = School.create(
            name="Colegio XYZ",
            address="456 Oak Avenue",
            now=now,
        )

        assert isinstance(school.id, SchoolId)
        assert isinstance(school.id.value, UUID)
        assert school.name == "Colegio XYZ"
        assert school.address == "456 Oak Avenue"
        assert school.created_at == now

    def test_create_strips_whitespace(self) -> None:
        """Test School.create() strips leading/trailing whitespace."""
        now = datetime.now(UTC)

        school = School.create(
            name="  Colegio ABC  ",
            address="  123 Main Street  ",
            now=now,
        )

        assert school.name == "Colegio ABC"
        assert school.address == "123 Main Street"


class TestSchoolValidation:
    """Tests for School entity validation."""

    def test_empty_name_raises_error(self) -> None:
        """Test that empty name raises InvalidSchoolDataError."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidSchoolDataError) as exc_info:
            School(
                id=school_id,
                name="",
                address="123 Main Street",
                created_at=now,
            )

        assert "name cannot be empty" in str(exc_info.value)

    def test_whitespace_only_name_raises_error(self) -> None:
        """Test that whitespace-only name raises InvalidSchoolDataError."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidSchoolDataError) as exc_info:
            School(
                id=school_id,
                name="   ",
                address="123 Main Street",
                created_at=now,
            )

        assert "name cannot be empty" in str(exc_info.value)

    def test_empty_address_raises_error(self) -> None:
        """Test that empty address raises InvalidSchoolDataError."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidSchoolDataError) as exc_info:
            School(
                id=school_id,
                name="Colegio ABC",
                address="",
                created_at=now,
            )

        assert "address cannot be empty" in str(exc_info.value)

    def test_whitespace_only_address_raises_error(self) -> None:
        """Test that whitespace-only address raises InvalidSchoolDataError."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        with pytest.raises(InvalidSchoolDataError) as exc_info:
            School(
                id=school_id,
                name="Colegio ABC",
                address="   ",
                created_at=now,
            )

        assert "address cannot be empty" in str(exc_info.value)

    def test_naive_datetime_raises_error(self) -> None:
        """Test that naive datetime (no timezone) raises InvalidSchoolDataError."""
        school_id = SchoolId.generate()
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)  # No timezone

        with pytest.raises(InvalidSchoolDataError) as exc_info:
            School(
                id=school_id,
                name="Colegio ABC",
                address="123 Main Street",
                created_at=naive_dt,
            )

        assert "UTC timezone" in str(exc_info.value)

    def test_non_utc_timezone_raises_error(self) -> None:
        """Test that non-UTC timezone raises InvalidSchoolDataError."""
        school_id = SchoolId.generate()
        eastern = timezone(timedelta(hours=-5))
        non_utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(InvalidSchoolDataError) as exc_info:
            School(
                id=school_id,
                name="Colegio ABC",
                address="123 Main Street",
                created_at=non_utc_dt,
            )

        assert "UTC timezone" in str(exc_info.value)


class TestSchoolImmutability:
    """Tests for School entity immutability."""

    def test_school_is_immutable(self) -> None:
        """Test that School attributes cannot be modified."""
        school = School.create(
            name="Colegio ABC",
            address="123 Main Street",
            now=datetime.now(UTC),
        )

        with pytest.raises(AttributeError):
            school.name = "New Name"  # type: ignore[misc]

    def test_school_is_hashable(self) -> None:
        """Test that School can be used in sets and as dict keys."""
        school = School.create(
            name="Colegio ABC",
            address="123 Main Street",
            now=datetime.now(UTC),
        )

        # Should not raise
        hash_value = hash(school)
        assert isinstance(hash_value, int)

        # Can be used in set
        school_set = {school}
        assert school in school_set


class TestSchoolEquality:
    """Tests for School entity equality."""

    def test_schools_with_same_data_are_equal(self) -> None:
        """Test that two schools with same data are equal."""
        school_id = SchoolId.generate()
        now = datetime.now(UTC)

        school1 = School(
            id=school_id,
            name="Colegio ABC",
            address="123 Main Street",
            created_at=now,
        )
        school2 = School(
            id=school_id,
            name="Colegio ABC",
            address="123 Main Street",
            created_at=now,
        )

        assert school1 == school2

    def test_schools_with_different_ids_are_not_equal(self) -> None:
        """Test that two schools with different IDs are not equal."""
        now = datetime.now(UTC)

        school1 = School.create(name="Colegio ABC", address="123 Main Street", now=now)
        school2 = School.create(name="Colegio ABC", address="123 Main Street", now=now)

        assert school1 != school2
