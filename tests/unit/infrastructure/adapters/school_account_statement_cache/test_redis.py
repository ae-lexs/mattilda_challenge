"""Unit tests for RedisSchoolAccountStatementCache.

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

from mattilda_challenge.application.dtos import SchoolAccountStatement
from mattilda_challenge.application.ports import SchoolAccountStatementCache
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.infrastructure.adapters.school_account_statement_cache import (
    RedisSchoolAccountStatementCache,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Provide mocked Redis client."""
    return AsyncMock()


@pytest.fixture
def fixed_school_id() -> SchoolId:
    """Provide fixed school ID for testing."""
    return SchoolId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_statement(
    fixed_school_id: SchoolId, fixed_time: datetime
) -> SchoolAccountStatement:
    """Provide sample school account statement for testing."""
    return SchoolAccountStatement(
        school_id=fixed_school_id,
        school_name="Test School",
        total_students=150,
        active_students=142,
        total_invoiced=Decimal("225000.00"),
        total_paid=Decimal("180000.00"),
        total_pending=Decimal("45000.00"),
        invoices_pending=25,
        invoices_partially_paid=10,
        invoices_paid=100,
        invoices_overdue=5,
        invoices_cancelled=3,
        total_late_fees=Decimal("1250.50"),
        statement_date=fixed_time,
    )


@pytest.fixture
def cache(mock_redis: AsyncMock) -> RedisSchoolAccountStatementCache:
    """Provide RedisSchoolAccountStatementCache with mocked Redis and settings."""
    with patch(
        "mattilda_challenge.infrastructure.adapters.school_account_statement_cache.redis.get_settings"
    ) as mock_get_settings:
        mock_get_settings.return_value.cache_ttl_seconds = 300
        return RedisSchoolAccountStatementCache(mock_redis)


# ============================================================================
# Interface Implementation
# ============================================================================


class TestRedisSchoolAccountStatementCacheInterface:
    """Tests for interface compliance."""

    def test_implements_cache_interface(
        self, cache: RedisSchoolAccountStatementCache
    ) -> None:
        """Test that RedisSchoolAccountStatementCache implements SchoolAccountStatementCache."""
        assert isinstance(cache, SchoolAccountStatementCache)


# ============================================================================
# Key Building
# ============================================================================


class TestRedisSchoolAccountStatementCacheKeyBuilding:
    """Tests for Redis key building."""

    def test_build_key_format(
        self,
        cache: RedisSchoolAccountStatementCache,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test _build_key produces correct key format."""
        key = cache._build_key(fixed_school_id)

        assert (
            key
            == "mattilda:cache:v1:account_statement:school:11111111-1111-1111-1111-111111111111"
        )

    def test_build_key_uses_key_prefix(
        self,
        cache: RedisSchoolAccountStatementCache,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test _build_key uses KEY_PREFIX constant."""
        key = cache._build_key(fixed_school_id)

        assert key.startswith(RedisSchoolAccountStatementCache.KEY_PREFIX)

    def test_build_key_different_ids_produce_different_keys(
        self,
        cache: RedisSchoolAccountStatementCache,
    ) -> None:
        """Test different school IDs produce different keys."""
        school_id_1 = SchoolId(value=UUID("11111111-1111-1111-1111-111111111111"))
        school_id_2 = SchoolId(value=UUID("22222222-2222-2222-2222-222222222222"))

        key_1 = cache._build_key(school_id_1)
        key_2 = cache._build_key(school_id_2)

        assert key_1 != key_2


# ============================================================================
# Serialization
# ============================================================================


class TestRedisSchoolAccountStatementCacheSerialization:
    """Tests for serialization and deserialization."""

    def test_serialize_returns_json_string(
        self,
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test _serialize returns valid JSON string."""
        result = cache._serialize(sample_statement)

        assert isinstance(result, str)
        # Should not raise
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_serialize_includes_all_fields(
        self,
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test _serialize includes all statement fields."""
        result = cache._serialize(sample_statement)
        parsed = json.loads(result)

        expected_fields = {
            "school_id",
            "school_name",
            "total_students",
            "active_students",
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
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test _serialize converts Decimal fields to strings for JSON."""
        result = cache._serialize(sample_statement)
        parsed = json.loads(result)

        assert parsed["total_invoiced"] == "225000.00"
        assert parsed["total_paid"] == "180000.00"
        assert parsed["total_pending"] == "45000.00"
        assert parsed["total_late_fees"] == "1250.50"

    def test_serialize_converts_datetime_to_iso_format(
        self,
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test _serialize converts datetime to ISO format."""
        result = cache._serialize(sample_statement)
        parsed = json.loads(result)

        assert parsed["statement_date"] == "2024-01-15T12:00:00+00:00"

    def test_deserialize_returns_statement(
        self,
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test _deserialize returns SchoolAccountStatement."""
        json_str = cache._serialize(sample_statement)

        result = cache._deserialize(json_str)

        assert isinstance(result, SchoolAccountStatement)

    def test_serialize_deserialize_round_trip(
        self,
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test serialization followed by deserialization preserves data."""
        json_str = cache._serialize(sample_statement)
        result = cache._deserialize(json_str)

        assert result.school_id == sample_statement.school_id
        assert result.school_name == sample_statement.school_name
        assert result.total_students == sample_statement.total_students
        assert result.active_students == sample_statement.active_students
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
        cache: RedisSchoolAccountStatementCache,
    ) -> None:
        """Test _deserialize preserves Decimal precision."""
        json_str = json.dumps(
            {
                "school_id": "11111111-1111-1111-1111-111111111111",
                "school_name": "Test",
                "total_students": 1,
                "active_students": 1,
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


class TestRedisSchoolAccountStatementCacheGet:
    """Tests for get method."""

    async def test_get_returns_statement_on_cache_hit(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: SchoolAccountStatement,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get returns deserialized statement on cache hit."""
        mock_redis.get.return_value = cache._serialize(sample_statement)

        result = await cache.get(fixed_school_id)

        assert result is not None
        assert result.school_id == fixed_school_id
        assert result.school_name == "Test School"

    async def test_get_returns_none_on_cache_miss(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get returns None when key not found."""
        mock_redis.get.return_value = None

        result = await cache.get(fixed_school_id)

        assert result is None

    async def test_get_calls_redis_with_correct_key(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get calls Redis with correctly formatted key."""
        mock_redis.get.return_value = None

        await cache.get(fixed_school_id)

        expected_key = (
            f"{RedisSchoolAccountStatementCache.KEY_PREFIX}:{fixed_school_id.value}"
        )
        mock_redis.get.assert_called_once_with(expected_key)

    async def test_get_returns_none_on_redis_error(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get returns None and logs warning on Redis error (fail-open)."""
        mock_redis.get.side_effect = RedisError("Connection refused")

        result = await cache.get(fixed_school_id)

        assert result is None

    async def test_get_returns_none_on_json_decode_error(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get returns None on invalid JSON (fail-open)."""
        mock_redis.get.return_value = "invalid json {"

        result = await cache.get(fixed_school_id)

        assert result is None

    async def test_get_returns_none_on_missing_field(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get returns None when cached data is missing fields (fail-open)."""
        mock_redis.get.return_value = json.dumps({"school_id": "123"})

        result = await cache.get(fixed_school_id)

        assert result is None

    async def test_get_returns_none_on_invalid_decimal(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test get returns None when decimal value is invalid (fail-open)."""
        mock_redis.get.return_value = json.dumps(
            {
                "school_id": "11111111-1111-1111-1111-111111111111",
                "school_name": "Test",
                "total_students": 1,
                "active_students": 1,
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

        result = await cache.get(fixed_school_id)

        assert result is None


# ============================================================================
# Set Method
# ============================================================================


class TestRedisSchoolAccountStatementCacheSet:
    """Tests for set method."""

    async def test_set_calls_redis_with_correct_key(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test set calls Redis with correctly formatted key."""
        await cache.set(sample_statement)

        expected_key = f"{RedisSchoolAccountStatementCache.KEY_PREFIX}:{sample_statement.school_id.value}"
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == expected_key

    async def test_set_calls_redis_with_serialized_data(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test set calls Redis with JSON serialized statement."""
        await cache.set(sample_statement)

        call_args = mock_redis.set.call_args
        serialized_data = call_args[0][1]
        # Should be valid JSON
        parsed = json.loads(serialized_data)
        assert parsed["school_name"] == "Test School"

    async def test_set_calls_redis_with_ttl(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test set calls Redis with TTL from settings."""
        await cache.set(sample_statement)

        call_args = mock_redis.set.call_args
        assert call_args[1]["ex"] == 300  # From mocked settings

    async def test_set_does_not_raise_on_redis_error(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test set does not raise on Redis error (fail-open)."""
        mock_redis.set.side_effect = RedisError("Connection refused")

        # Should not raise
        await cache.set(sample_statement)

    async def test_set_completes_successfully(
        self,
        cache: RedisSchoolAccountStatementCache,
        mock_redis: AsyncMock,
        sample_statement: SchoolAccountStatement,
    ) -> None:
        """Test set completes without error on success."""
        mock_redis.set.return_value = True

        # Should not raise
        await cache.set(sample_statement)

        mock_redis.set.assert_called_once()
