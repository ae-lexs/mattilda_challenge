"""Unit tests for RedisStudentAccountStatementCache.

These tests verify the Redis cache implementation logic using mocked
Redis client. Integration tests verify actual Redis behavior.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from redis.exceptions import RedisError

from mattilda_challenge.application.dtos import StudentAccountStatement
from mattilda_challenge.application.ports import StudentAccountStatementCache
from mattilda_challenge.domain.value_objects import StudentId
from mattilda_challenge.infrastructure.adapters.student_account_statement_cache import (
    RedisStudentAccountStatementCache,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Provide mocked Redis client."""
    return AsyncMock()


@pytest.fixture
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_statement(
    fixed_student_id: StudentId, fixed_time: datetime
) -> StudentAccountStatement:
    """Provide sample student account statement for testing."""
    return StudentAccountStatement(
        student_id=fixed_student_id,
        student_name="Test Student",
        school_name="Test School",
        total_invoiced=Decimal("4500.00"),
        total_paid=Decimal("3000.00"),
        total_pending=Decimal("1500.00"),
        invoices_pending=3,
        invoices_partially_paid=1,
        invoices_paid=5,
        invoices_overdue=2,
        invoices_cancelled=1,
        total_late_fees=Decimal("125.50"),
        statement_date=fixed_time,
    )


@pytest.fixture
def cache(mock_redis: AsyncMock) -> RedisStudentAccountStatementCache:
    """Provide RedisStudentAccountStatementCache with mocked Redis and settings."""
    with patch(
        "mattilda_challenge.infrastructure.adapters.student_account_statement_cache.redis.get_settings"
    ) as mock_get_settings:
        mock_get_settings.return_value.cache_ttl_seconds = 300
        return RedisStudentAccountStatementCache(mock_redis)


# ============================================================================
# Interface Implementation
# ============================================================================


class TestRedisStudentAccountStatementCacheInterface:
    """Tests for interface compliance."""

    def test_implements_cache_interface(
        self, cache: RedisStudentAccountStatementCache
    ) -> None:
        """Test that RedisStudentAccountStatementCache implements StudentAccountStatementCache."""
        assert isinstance(cache, StudentAccountStatementCache)


# ============================================================================
# Key Building
# ============================================================================


class TestRedisStudentAccountStatementCacheKeyBuilding:
    """Tests for Redis key building."""

    def test_build_key_format(
        self,
        cache: RedisStudentAccountStatementCache,
        fixed_student_id: StudentId,
    ) -> None:
        """Test _build_key produces correct key format."""
        key = cache._build_key(fixed_student_id)

        assert (
            key
            == "mattilda:cache:v1:account_statement:student:11111111-1111-1111-1111-111111111111"
        )

    def test_build_key_uses_key_prefix(
        self,
        cache: RedisStudentAccountStatementCache,
        fixed_student_id: StudentId,
    ) -> None:
        """Test _build_key uses KEY_PREFIX constant."""
        key = cache._build_key(fixed_student_id)

        assert key.startswith(RedisStudentAccountStatementCache.KEY_PREFIX)

    def test_build_key_different_ids_produce_different_keys(
        self,
        cache: RedisStudentAccountStatementCache,
    ) -> None:
        """Test different student IDs produce different keys."""
        student_id_1 = StudentId(value=UUID("11111111-1111-1111-1111-111111111111"))
        student_id_2 = StudentId(value=UUID("22222222-2222-2222-2222-222222222222"))

        key_1 = cache._build_key(student_id_1)
        key_2 = cache._build_key(student_id_2)

        assert key_1 != key_2


# ============================================================================
# Serialization
# ============================================================================


class TestRedisStudentAccountStatementCacheSerialization:
    """Tests for serialization and deserialization."""

    def test_serialize_returns_json_string(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test _serialize returns valid JSON string."""
        result = cache._serialize(sample_statement)

        assert isinstance(result, str)
        # Should not raise
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_serialize_includes_all_fields(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test _serialize includes all statement fields."""
        result = cache._serialize(sample_statement)
        parsed = json.loads(result)

        expected_fields = {
            "student_id",
            "student_name",
            "school_name",
            "total_invoiced",
            "total_paid",
            "total_pending",
            "invoices_pending",
            "invoices_partially_paid",
            "invoices_paid",
            "invoices_overdue",
            "invoices_cancelled",
            "total_late_fees",
            "statement_date",
        }
        assert set(parsed.keys()) == expected_fields

    def test_serialize_converts_decimals_to_strings(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test _serialize converts Decimal fields to strings for JSON."""
        result = cache._serialize(sample_statement)
        parsed = json.loads(result)

        assert parsed["total_invoiced"] == "4500.00"
        assert parsed["total_paid"] == "3000.00"
        assert parsed["total_pending"] == "1500.00"
        assert parsed["total_late_fees"] == "125.50"

    def test_serialize_converts_datetime_to_iso_format(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test _serialize converts datetime to ISO format."""
        result = cache._serialize(sample_statement)
        parsed = json.loads(result)

        assert parsed["statement_date"] == "2024-01-15T12:00:00+00:00"

    def test_deserialize_returns_statement(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test _deserialize returns StudentAccountStatement."""
        json_str = cache._serialize(sample_statement)

        result = cache._deserialize(json_str)

        assert isinstance(result, StudentAccountStatement)

    def test_serialize_deserialize_round_trip(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test serialization followed by deserialization preserves data."""
        json_str = cache._serialize(sample_statement)
        result = cache._deserialize(json_str)

        assert result.student_id == sample_statement.student_id
        assert result.student_name == sample_statement.student_name
        assert result.school_name == sample_statement.school_name
        assert result.total_invoiced == sample_statement.total_invoiced
        assert result.total_paid == sample_statement.total_paid
        assert result.total_pending == sample_statement.total_pending
        assert result.invoices_pending == sample_statement.invoices_pending
        assert (
            result.invoices_partially_paid == sample_statement.invoices_partially_paid
        )
        assert result.invoices_paid == sample_statement.invoices_paid
        assert result.invoices_overdue == sample_statement.invoices_overdue
        assert result.invoices_cancelled == sample_statement.invoices_cancelled
        assert result.total_late_fees == sample_statement.total_late_fees
        assert result.statement_date == sample_statement.statement_date

    def test_deserialize_preserves_decimal_precision(
        self,
        cache: RedisStudentAccountStatementCache,
    ) -> None:
        """Test _deserialize preserves Decimal precision."""
        json_str = json.dumps(
            {
                "student_id": "11111111-1111-1111-1111-111111111111",
                "student_name": "Test",
                "school_name": "Test School",
                "total_invoiced": "1234.56",
                "total_paid": "1000.00",
                "total_pending": "234.56",
                "invoices_pending": 1,
                "invoices_partially_paid": 0,
                "invoices_paid": 0,
                "invoices_overdue": 0,
                "invoices_cancelled": 0,
                "total_late_fees": "0.01",
                "statement_date": "2024-01-15T12:00:00+00:00",
            }
        )

        result = cache._deserialize(json_str)

        assert result.total_invoiced == Decimal("1234.56")
        assert result.total_late_fees == Decimal("0.01")
        assert isinstance(result.total_invoiced, Decimal)


# ============================================================================
# Get Method
# ============================================================================


class TestRedisStudentAccountStatementCacheGet:
    """Tests for get method."""

    async def test_get_returns_statement_on_cache_hit(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: StudentAccountStatement,
        fixed_student_id: StudentId,
    ) -> None:
        """Test get returns deserialized statement on cache hit."""
        mock_redis.get.return_value = cache._serialize(sample_statement)

        result = await cache.get(fixed_student_id)

        assert result is not None
        assert result.student_id == fixed_student_id
        assert result.student_name == "Test Student"

    async def test_get_returns_none_on_cache_miss(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_student_id: StudentId,
    ) -> None:
        """Test get returns None when key not found."""
        mock_redis.get.return_value = None

        result = await cache.get(fixed_student_id)

        assert result is None

    async def test_get_calls_redis_with_correct_key(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_student_id: StudentId,
    ) -> None:
        """Test get calls Redis with correctly formatted key."""
        mock_redis.get.return_value = None

        await cache.get(fixed_student_id)

        expected_key = (
            f"{RedisStudentAccountStatementCache.KEY_PREFIX}:{fixed_student_id.value}"
        )
        mock_redis.get.assert_called_once_with(expected_key)

    async def test_get_returns_none_on_redis_error(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_student_id: StudentId,
    ) -> None:
        """Test get returns None and logs warning on Redis error (fail-open)."""
        mock_redis.get.side_effect = RedisError("Connection refused")

        result = await cache.get(fixed_student_id)

        assert result is None

    async def test_get_returns_none_on_json_decode_error(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_student_id: StudentId,
    ) -> None:
        """Test get returns None on invalid JSON (fail-open)."""
        mock_redis.get.return_value = "invalid json {"

        result = await cache.get(fixed_student_id)

        assert result is None

    async def test_get_returns_none_on_missing_field(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_student_id: StudentId,
    ) -> None:
        """Test get returns None when cached data is missing fields (fail-open)."""
        mock_redis.get.return_value = json.dumps({"student_id": "123"})

        result = await cache.get(fixed_student_id)

        assert result is None

    async def test_get_returns_none_on_invalid_decimal(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_student_id: StudentId,
    ) -> None:
        """Test get returns None when decimal value is invalid (fail-open)."""
        mock_redis.get.return_value = json.dumps(
            {
                "student_id": "11111111-1111-1111-1111-111111111111",
                "student_name": "Test",
                "school_name": "Test School",
                "total_invoiced": "not_a_decimal",
                "total_paid": "0",
                "total_pending": "0",
                "invoices_pending": 0,
                "invoices_partially_paid": 0,
                "invoices_paid": 0,
                "invoices_overdue": 0,
                "invoices_cancelled": 0,
                "total_late_fees": "0",
                "statement_date": "2024-01-15T12:00:00+00:00",
            }
        )

        result = await cache.get(fixed_student_id)

        assert result is None


# ============================================================================
# Set Method
# ============================================================================


class TestRedisStudentAccountStatementCacheSet:
    """Tests for set method."""

    async def test_set_calls_redis_with_correct_key(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test set calls Redis with correctly formatted key."""
        await cache.set(sample_statement)

        expected_key = f"{RedisStudentAccountStatementCache.KEY_PREFIX}:{sample_statement.student_id.value}"
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == expected_key

    async def test_set_calls_redis_with_serialized_data(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test set calls Redis with JSON serialized statement."""
        await cache.set(sample_statement)

        call_args = mock_redis.set.call_args
        serialized_data = call_args[0][1]
        # Should be valid JSON
        parsed = json.loads(serialized_data)
        assert parsed["student_name"] == "Test Student"

    async def test_set_calls_redis_with_ttl(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test set calls Redis with TTL from settings."""
        await cache.set(sample_statement)

        call_args = mock_redis.set.call_args
        assert call_args[1]["ex"] == 300  # From mocked settings

    async def test_set_does_not_raise_on_redis_error(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test set does not raise on Redis error (fail-open)."""
        mock_redis.set.side_effect = RedisError("Connection refused")

        # Should not raise
        await cache.set(sample_statement)

    async def test_set_completes_successfully(
        self,
        cache: RedisStudentAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: StudentAccountStatement,
    ) -> None:
        """Test set completes without error on success."""
        mock_redis.set.return_value = True

        # Should not raise
        await cache.set(sample_statement)

        mock_redis.set.assert_called_once()
