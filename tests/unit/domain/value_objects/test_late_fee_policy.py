"""Tests for LateFeePolicy value object."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from mattilda_challenge.domain.exceptions import (
    InvalidLateFeeRateError,
    InvalidTimestampError,
)
from mattilda_challenge.domain.value_objects.late_fee_policy import LateFeePolicy


class TestLateFeePolicyCreation:
    """Tests for LateFeePolicy creation and validation."""

    def test_create_with_valid_decimal_rate(self) -> None:
        """Test creating policy with valid Decimal rate."""
        policy = LateFeePolicy(monthly_rate=Decimal("0.05"))

        assert policy.monthly_rate == Decimal("0.05")

    def test_create_with_zero_rate(self) -> None:
        """Test creating policy with zero rate."""
        policy = LateFeePolicy(monthly_rate=Decimal("0"))

        assert policy.monthly_rate == Decimal("0")

    def test_create_with_max_rate(self) -> None:
        """Test creating policy with maximum rate (1.0 = 100%)."""
        policy = LateFeePolicy(monthly_rate=Decimal("1"))

        assert policy.monthly_rate == Decimal("1")

    def test_non_decimal_rate_raises_error(self) -> None:
        """Test that non-Decimal rate raises InvalidLateFeeRateError."""
        with pytest.raises(InvalidLateFeeRateError) as exc_info:
            LateFeePolicy(monthly_rate=0.05)  # type: ignore[arg-type]

        assert "must be Decimal" in str(exc_info.value)
        assert "float" in str(exc_info.value)

    def test_negative_rate_raises_error(self) -> None:
        """Test that negative rate raises InvalidLateFeeRateError."""
        with pytest.raises(InvalidLateFeeRateError) as exc_info:
            LateFeePolicy(monthly_rate=Decimal("-0.01"))

        assert "must be between 0 and 1" in str(exc_info.value)

    def test_rate_greater_than_one_raises_error(self) -> None:
        """Test that rate > 1 raises InvalidLateFeeRateError."""
        with pytest.raises(InvalidLateFeeRateError) as exc_info:
            LateFeePolicy(monthly_rate=Decimal("1.01"))

        assert "must be between 0 and 1" in str(exc_info.value)


class TestLateFeePolicyFactoryMethods:
    """Tests for LateFeePolicy factory methods."""

    def test_standard_returns_five_percent(self) -> None:
        """Test standard() returns 5% monthly rate policy."""
        policy = LateFeePolicy.standard()

        assert policy.monthly_rate == Decimal("0.05")

    def test_no_late_fees_returns_zero_percent(self) -> None:
        """Test no_late_fees() returns 0% rate policy."""
        policy = LateFeePolicy.no_late_fees()

        assert policy.monthly_rate == Decimal("0.00")


class TestLateFeePolicyCalculation:
    """Tests for LateFeePolicy.calculate_fee method."""

    def test_not_overdue_returns_zero(self) -> None:
        """Test that non-overdue invoice returns zero fee."""
        policy = LateFeePolicy.standard()
        due_date = datetime(2024, 1, 15, tzinfo=UTC)
        now = datetime(2024, 1, 14, tzinfo=UTC)  # Before due date

        fee = policy.calculate_fee(
            original_amount=Decimal("1500.00"),
            due_date=due_date,
            now=now,
        )

        assert fee == Decimal("0.00")

    def test_same_day_returns_zero(self) -> None:
        """Test that same day as due date returns zero fee."""
        policy = LateFeePolicy.standard()
        due_date = datetime(2024, 1, 15, tzinfo=UTC)
        now = datetime(2024, 1, 15, tzinfo=UTC)  # Same day

        fee = policy.calculate_fee(
            original_amount=Decimal("1500.00"),
            due_date=due_date,
            now=now,
        )

        assert fee == Decimal("0.00")

    def test_one_day_overdue(self) -> None:
        """Test fee calculation for 1 day overdue."""
        policy = LateFeePolicy.standard()  # 5% monthly
        due_date = datetime(2024, 1, 15, tzinfo=UTC)
        now = datetime(2024, 1, 16, tzinfo=UTC)  # 1 day overdue

        fee = policy.calculate_fee(
            original_amount=Decimal("1500.00"),
            due_date=due_date,
            now=now,
        )

        # 1500 × 0.05 / 30 × 1 = 2.50
        assert fee == Decimal("2.50")

    def test_fifteen_days_overdue(self) -> None:
        """Test fee calculation for 15 days overdue (ADR-002 example)."""
        policy = LateFeePolicy.standard()  # 5% monthly
        due_date = datetime(2024, 1, 1, tzinfo=UTC)
        now = datetime(2024, 1, 16, tzinfo=UTC)  # 15 days overdue

        fee = policy.calculate_fee(
            original_amount=Decimal("1500.00"),
            due_date=due_date,
            now=now,
        )

        # 1500 × 0.05 / 30 × 15 = 37.50
        assert fee == Decimal("37.50")

    def test_thirty_days_overdue(self) -> None:
        """Test fee calculation for 30 days (full month) overdue."""
        policy = LateFeePolicy.standard()  # 5% monthly
        due_date = datetime(2024, 1, 1, tzinfo=UTC)
        now = datetime(2024, 1, 31, tzinfo=UTC)  # 30 days overdue

        fee = policy.calculate_fee(
            original_amount=Decimal("1500.00"),
            due_date=due_date,
            now=now,
        )

        # 1500 × 0.05 / 30 × 30 = 75.00
        assert fee == Decimal("75.00")

    def test_sixty_days_overdue(self) -> None:
        """Test fee calculation for 60 days (two months) overdue."""
        policy = LateFeePolicy.standard()  # 5% monthly
        due_date = datetime(2024, 1, 1, tzinfo=UTC)
        now = datetime(2024, 3, 1, tzinfo=UTC)  # 60 days overdue

        fee = policy.calculate_fee(
            original_amount=Decimal("1500.00"),
            due_date=due_date,
            now=now,
        )

        # 1500 × 0.05 / 30 × 60 = 150.00
        assert fee == Decimal("150.00")

    def test_zero_rate_returns_zero(self) -> None:
        """Test that zero rate policy returns zero fee even when overdue."""
        policy = LateFeePolicy.no_late_fees()
        due_date = datetime(2024, 1, 1, tzinfo=UTC)
        now = datetime(2024, 2, 1, tzinfo=UTC)  # 31 days overdue

        fee = policy.calculate_fee(
            original_amount=Decimal("1500.00"),
            due_date=due_date,
            now=now,
        )

        assert fee == Decimal("0.00")

    def test_rounding_half_up(self) -> None:
        """Test that fees are rounded using ROUND_HALF_UP."""
        policy = LateFeePolicy(monthly_rate=Decimal("0.07"))  # 7%
        due_date = datetime(2024, 1, 1, tzinfo=UTC)
        now = datetime(2024, 1, 8, tzinfo=UTC)  # 7 days overdue

        fee = policy.calculate_fee(
            original_amount=Decimal("100.00"),
            due_date=due_date,
            now=now,
        )

        # 100 × 0.07 / 30 × 7 = 1.633333...
        # Rounded to 1.63
        assert fee == Decimal("1.63")

    def test_rounding_edge_case(self) -> None:
        """Test rounding when result is exactly 0.5 cents."""
        # Create a scenario where we get exactly X.XX5
        policy = LateFeePolicy(monthly_rate=Decimal("0.03"))  # 3%
        due_date = datetime(2024, 1, 1, tzinfo=UTC)
        now = datetime(2024, 1, 6, tzinfo=UTC)  # 5 days overdue

        fee = policy.calculate_fee(
            original_amount=Decimal("100.00"),
            due_date=due_date,
            now=now,
        )

        # 100 × 0.03 / 30 × 5 = 0.50
        assert fee == Decimal("0.50")

    def test_uses_original_amount_not_balance(self) -> None:
        """Test that fee is based on original amount (business rule)."""
        policy = LateFeePolicy.standard()
        due_date = datetime(2024, 1, 1, tzinfo=UTC)
        now = datetime(2024, 1, 16, tzinfo=UTC)  # 15 days

        # Even if balance due is different, fee uses original amount
        fee = policy.calculate_fee(
            original_amount=Decimal("1500.00"),  # Original invoice
            due_date=due_date,
            now=now,
        )

        # Fee is on $1500, not on any partial balance
        assert fee == Decimal("37.50")


class TestLateFeePolicyTimestampValidation:
    """Tests for LateFeePolicy timestamp validation."""

    def test_naive_due_date_raises_error(self) -> None:
        """Test that naive due_date raises InvalidTimestampError."""
        policy = LateFeePolicy.standard()
        naive_due_date = datetime(2024, 1, 1)  # No timezone
        now = datetime(2024, 1, 16, tzinfo=UTC)

        with pytest.raises(InvalidTimestampError) as exc_info:
            policy.calculate_fee(
                original_amount=Decimal("1500.00"),
                due_date=naive_due_date,
                now=now,
            )

        assert "due_date" in str(exc_info.value)

    def test_naive_now_raises_error(self) -> None:
        """Test that naive now raises InvalidTimestampError."""
        policy = LateFeePolicy.standard()
        due_date = datetime(2024, 1, 1, tzinfo=UTC)
        naive_now = datetime(2024, 1, 16)  # No timezone

        with pytest.raises(InvalidTimestampError) as exc_info:
            policy.calculate_fee(
                original_amount=Decimal("1500.00"),
                due_date=due_date,
                now=naive_now,
            )

        assert "now" in str(exc_info.value)

    def test_non_utc_due_date_raises_error(self) -> None:
        """Test that non-UTC due_date raises InvalidTimestampError."""
        policy = LateFeePolicy.standard()
        eastern = timezone(timedelta(hours=-5))
        non_utc_due_date = datetime(2024, 1, 1, tzinfo=eastern)
        now = datetime(2024, 1, 16, tzinfo=UTC)

        with pytest.raises(InvalidTimestampError) as exc_info:
            policy.calculate_fee(
                original_amount=Decimal("1500.00"),
                due_date=non_utc_due_date,
                now=now,
            )

        assert "due_date" in str(exc_info.value)

    def test_non_utc_now_raises_error(self) -> None:
        """Test that non-UTC now raises InvalidTimestampError."""
        policy = LateFeePolicy.standard()
        due_date = datetime(2024, 1, 1, tzinfo=UTC)
        eastern = timezone(timedelta(hours=-5))
        non_utc_now = datetime(2024, 1, 16, tzinfo=eastern)

        with pytest.raises(InvalidTimestampError) as exc_info:
            policy.calculate_fee(
                original_amount=Decimal("1500.00"),
                due_date=due_date,
                now=non_utc_now,
            )

        assert "now" in str(exc_info.value)


class TestLateFeePolicyImmutability:
    """Tests for LateFeePolicy immutability."""

    def test_policy_is_immutable(self) -> None:
        """Test that policy attributes cannot be modified."""
        policy = LateFeePolicy.standard()

        with pytest.raises(AttributeError):
            policy.monthly_rate = Decimal("0.10")  # type: ignore[misc]

    def test_policy_is_hashable(self) -> None:
        """Test that policy can be used in sets and as dict keys."""
        policy = LateFeePolicy.standard()

        hash_value = hash(policy)
        assert isinstance(hash_value, int)

        policy_set = {policy}
        assert policy in policy_set

    def test_equal_policies_are_equal(self) -> None:
        """Test that policies with same rate are equal."""
        policy1 = LateFeePolicy(monthly_rate=Decimal("0.05"))
        policy2 = LateFeePolicy(monthly_rate=Decimal("0.05"))

        assert policy1 == policy2

    def test_different_policies_are_not_equal(self) -> None:
        """Test that policies with different rates are not equal."""
        policy1 = LateFeePolicy(monthly_rate=Decimal("0.05"))
        policy2 = LateFeePolicy(monthly_rate=Decimal("0.10"))

        assert policy1 != policy2
