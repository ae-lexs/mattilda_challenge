"""Tests for time provider adapters."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from mattilda_challenge.application.ports import TimeProvider
from mattilda_challenge.infrastructure.adapters import (
    FixedTimeProvider,
    SystemTimeProvider,
)


class TestSystemTimeProvider:
    """Tests for SystemTimeProvider implementation."""

    def test_implements_time_provider_interface(self) -> None:
        """Test that SystemTimeProvider implements TimeProvider."""
        provider = SystemTimeProvider()
        assert isinstance(provider, TimeProvider)

    def test_now_returns_datetime(self) -> None:
        """Test that now() returns a datetime object."""
        provider = SystemTimeProvider()
        result = provider.now()
        assert isinstance(result, datetime)

    def test_now_returns_utc_timezone(self) -> None:
        """Test that now() returns datetime with UTC timezone."""
        provider = SystemTimeProvider()
        result = provider.now()
        assert result.tzinfo is UTC

    def test_now_is_not_naive(self) -> None:
        """Test that now() never returns a naive datetime."""
        provider = SystemTimeProvider()
        result = provider.now()
        assert result.tzinfo is not None

    def test_now_returns_current_time(self) -> None:
        """Test that now() returns approximately the current time."""
        provider = SystemTimeProvider()
        before = datetime.now(UTC)
        result = provider.now()
        after = datetime.now(UTC)

        assert before <= result <= after

    def test_successive_calls_increase(self) -> None:
        """Test that successive calls return non-decreasing times."""
        provider = SystemTimeProvider()
        first = provider.now()
        second = provider.now()

        assert second >= first

    def test_multiple_instances_return_consistent_time(self) -> None:
        """Test that different instances return consistent times."""
        provider1 = SystemTimeProvider()
        provider2 = SystemTimeProvider()

        time1 = provider1.now()
        time2 = provider2.now()

        # Times should be within 1 second of each other
        assert abs((time2 - time1).total_seconds()) < 1


class TestFixedTimeProvider:
    """Tests for FixedTimeProvider implementation."""

    def test_implements_time_provider_interface(self) -> None:
        """Test that FixedTimeProvider implements TimeProvider."""
        fixed_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        provider = FixedTimeProvider(fixed_time)
        assert isinstance(provider, TimeProvider)

    def test_now_returns_fixed_time(self) -> None:
        """Test that now() returns the fixed time provided at construction."""
        fixed_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        provider = FixedTimeProvider(fixed_time)

        result = provider.now()

        assert result == fixed_time

    def test_now_returns_utc_timezone(self) -> None:
        """Test that now() returns datetime with UTC timezone."""
        fixed_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        provider = FixedTimeProvider(fixed_time)

        result = provider.now()

        assert result.tzinfo is UTC

    def test_multiple_calls_return_same_time(self) -> None:
        """Test that multiple calls return the same fixed time."""
        fixed_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        provider = FixedTimeProvider(fixed_time)

        first = provider.now()
        second = provider.now()
        third = provider.now()

        assert first == second == third == fixed_time

    def test_set_time_changes_returned_time(self) -> None:
        """Test that set_time() changes what now() returns."""
        initial_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        new_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)
        provider = FixedTimeProvider(initial_time)

        provider.set_time(new_time)
        result = provider.now()

        assert result == new_time

    def test_set_time_allows_time_travel_forward(self) -> None:
        """Test simulating time passing forward."""
        start_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        provider = FixedTimeProvider(start_time)

        # Simulate 30 days passing
        future_time = start_time + timedelta(days=30)
        provider.set_time(future_time)

        assert provider.now() == future_time

    def test_set_time_allows_time_travel_backward(self) -> None:
        """Test simulating going back in time (useful for edge case testing)."""
        start_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        provider = FixedTimeProvider(start_time)

        # Go back to the past
        past_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        provider.set_time(past_time)

        assert provider.now() == past_time


class TestFixedTimeProviderValidation:
    """Tests for FixedTimeProvider validation."""

    def test_constructor_rejects_naive_datetime(self) -> None:
        """Test that constructor rejects naive datetime."""
        naive_time = datetime(2024, 1, 15, 12, 0, 0)

        with pytest.raises(ValueError) as exc_info:
            FixedTimeProvider(naive_time)

        assert "must have tzinfo=UTC" in str(exc_info.value)
        assert "tzinfo=None" in str(exc_info.value)

    def test_constructor_rejects_non_utc_timezone(self) -> None:
        """Test that constructor rejects non-UTC timezone."""
        eastern = timezone(timedelta(hours=-5))
        non_utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(ValueError) as exc_info:
            FixedTimeProvider(non_utc_time)

        assert "must have tzinfo=UTC" in str(exc_info.value)

    def test_set_time_rejects_naive_datetime(self) -> None:
        """Test that set_time() rejects naive datetime."""
        provider = FixedTimeProvider(datetime(2024, 1, 1, tzinfo=UTC))
        naive_time = datetime(2024, 1, 15, 12, 0, 0)

        with pytest.raises(ValueError) as exc_info:
            provider.set_time(naive_time)

        assert "must have tzinfo=UTC" in str(exc_info.value)

    def test_set_time_rejects_non_utc_timezone(self) -> None:
        """Test that set_time() rejects non-UTC timezone."""
        provider = FixedTimeProvider(datetime(2024, 1, 1, tzinfo=UTC))
        eastern = timezone(timedelta(hours=-5))
        non_utc_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=eastern)

        with pytest.raises(ValueError) as exc_info:
            provider.set_time(non_utc_time)

        assert "must have tzinfo=UTC" in str(exc_info.value)
