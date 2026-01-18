"""Tests for validate_utc_timestamp function."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from mattilda_challenge.domain.exceptions import InvalidTimestampError
from mattilda_challenge.domain.validate_utc_timestamp import validate_utc_timestamp


class TestValidateUtcTimestamp:
    """Tests for validate_utc_timestamp function."""

    def test_valid_utc_datetime_passes(self) -> None:
        """Test that UTC datetime passes validation without raising."""
        utc_dt = datetime.now(UTC)

        # Should not raise
        validate_utc_timestamp(utc_dt, "created_at")

    def test_valid_utc_datetime_explicit(self) -> None:
        """Test that explicit UTC timezone passes validation."""
        utc_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)

        # Should not raise
        validate_utc_timestamp(utc_dt, "updated_at")

    def test_naive_datetime_raises_error(self) -> None:
        """Test that naive datetime raises InvalidTimestampError."""
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)

        with pytest.raises(InvalidTimestampError) as exc_info:
            validate_utc_timestamp(naive_dt, "created_at")

        assert "must be timezone-aware" in str(exc_info.value)
        assert "naive datetime" in str(exc_info.value)
        assert "created_at" in str(exc_info.value)

    def test_non_utc_timezone_raises_error(self) -> None:
        """Test that non-UTC timezone raises InvalidTimestampError."""
        eastern = timezone(timedelta(hours=-5))
        eastern_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(InvalidTimestampError) as exc_info:
            validate_utc_timestamp(eastern_dt, "due_date")

        assert "must have UTC timezone" in str(exc_info.value)
        assert "due_date" in str(exc_info.value)

    def test_positive_offset_timezone_raises_error(self) -> None:
        """Test that positive offset timezone raises error."""
        tokyo = timezone(timedelta(hours=9))
        tokyo_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=tokyo)

        with pytest.raises(InvalidTimestampError) as exc_info:
            validate_utc_timestamp(tokyo_dt, "payment_date")

        assert "must have UTC timezone" in str(exc_info.value)
        assert "payment_date" in str(exc_info.value)

    def test_field_name_included_in_naive_error(self) -> None:
        """Test that field name is included in error for naive datetime."""
        naive_dt = datetime(2024, 1, 15, 12, 0, 0)

        with pytest.raises(InvalidTimestampError) as exc_info:
            validate_utc_timestamp(naive_dt, "enrollment_date")

        assert "enrollment_date" in str(exc_info.value)

    def test_field_name_included_in_non_utc_error(self) -> None:
        """Test that field name is included in error for non-UTC timezone."""
        eastern = timezone(timedelta(hours=-5))
        eastern_dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(InvalidTimestampError) as exc_info:
            validate_utc_timestamp(eastern_dt, "statement_date")

        assert "statement_date" in str(exc_info.value)

    def test_datetime_value_included_in_error(self) -> None:
        """Test that datetime value is included in error message."""
        naive_dt = datetime(2024, 1, 15, 12, 30, 45)

        with pytest.raises(InvalidTimestampError) as exc_info:
            validate_utc_timestamp(naive_dt, "test_field")

        # The datetime string representation should be in the error
        assert "2024-01-15" in str(exc_info.value)
