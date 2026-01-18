"""Integration tests for RedisSchoolAccountStatementCache.

These tests verify the Redis cache implementation against a real Redis instance.
Per ADR-009, integration tests are required for infrastructure adapters that
interact with external services.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from redis.asyncio import Redis

from mattilda_challenge.application.dtos import SchoolAccountStatement
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.infrastructure.adapters.school_account_statement_cache import (
    RedisSchoolAccountStatementCache,
)

pytestmark = pytest.mark.integration

# Redis URL - uses Docker service name in CI, localhost otherwise
_redis_host = os.getenv("REDIS_HOST", "redis")
REDIS_URL = f"redis://{_redis_host}:6379/1"  # Use DB 1 for tests


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def redis_client() -> Redis:
    """Provide Redis client for tests."""
    client = Redis.from_url(REDIS_URL, decode_responses=True)
    yield client
    await client.aclose()


@pytest.fixture
async def cache(redis_client: Redis) -> RedisSchoolAccountStatementCache:
    """Provide RedisSchoolAccountStatementCache with real Redis."""
    # Patch settings for test TTL
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "mattilda_challenge.infrastructure.adapters.school_account_statement_cache.redis._settings.cache_ttl_seconds",
            300,
        )
        yield RedisSchoolAccountStatementCache(redis_client)


@pytest.fixture
async def cleanup_cache(redis_client: Redis):
    """Clean up test keys before and after each test."""
    pattern = f"{RedisSchoolAccountStatementCache.KEY_PREFIX}:*"

    # Cleanup before test
    keys = []
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key)
    if keys:
        await redis_client.delete(*keys)

    yield

    # Cleanup after test
    keys = []
    async for key in redis_client.scan_iter(match=pattern):
        keys.append(key)
    if keys:
        await redis_client.delete(*keys)


@pytest.fixture
def fixed_school_id() -> SchoolId:
    """Provide fixed school ID for testing."""
    return SchoolId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def fixed_school_id_2() -> SchoolId:
    """Provide second fixed school ID for testing."""
    return SchoolId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_statement(
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> SchoolAccountStatement:
    """Provide sample school account statement for testing."""
    return SchoolAccountStatement(
        school_id=fixed_school_id,
        school_name="Integration Test School",
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
def sample_statement_2(
    fixed_school_id_2: SchoolId,
    fixed_time: datetime,
) -> SchoolAccountStatement:
    """Provide second sample statement for testing."""
    return SchoolAccountStatement(
        school_id=fixed_school_id_2,
        school_name="Second Test School",
        total_students=75,
        active_students=70,
        total_invoiced=Decimal("112500.00"),
        total_paid=Decimal("90000.00"),
        total_pending=Decimal("22500.00"),
        invoices_pending=12,
        invoices_partially_paid=5,
        invoices_paid=50,
        invoices_overdue=2,
        invoices_cancelled=1,
        total_late_fees=Decimal("625.25"),
        statement_date=fixed_time,
    )


# ============================================================================
# Basic Operations
# ============================================================================


class TestRedisSchoolAccountStatementCacheSetGet:
    """Integration tests for set and get operations."""

    async def test_set_then_get_returns_statement(
        self,
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
        fixed_school_id: SchoolId,
        cleanup_cache: None,
    ) -> None:
        """Test set followed by get returns the cached statement."""
        await cache.set(sample_statement)

        result = await cache.get(fixed_school_id)

        assert result is not None
        assert result.school_id == fixed_school_id
        assert result.school_name == "Integration Test School"

    async def test_get_returns_none_when_not_cached(
        self,
        cache: RedisSchoolAccountStatementCache,
        fixed_school_id: SchoolId,
        cleanup_cache: None,
    ) -> None:
        """Test get returns None when key doesn't exist."""
        result = await cache.get(fixed_school_id)

        assert result is None

    async def test_set_overwrites_existing_cache(
        self,
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
        cleanup_cache: None,
    ) -> None:
        """Test set overwrites previously cached statement."""
        await cache.set(sample_statement)

        updated_statement = SchoolAccountStatement(
            school_id=fixed_school_id,
            school_name="Updated School Name",
            total_students=200,
            active_students=190,
            total_invoiced=Decimal("300000.00"),
            total_paid=Decimal("250000.00"),
            total_pending=Decimal("50000.00"),
            invoices_pending=30,
            invoices_partially_paid=15,
            invoices_paid=120,
            invoices_overdue=8,
            invoices_cancelled=5,
            total_late_fees=Decimal("2000.00"),
            statement_date=fixed_time,
        )
        await cache.set(updated_statement)

        result = await cache.get(fixed_school_id)

        assert result is not None
        assert result.school_name == "Updated School Name"
        assert result.total_students == 200

    async def test_different_schools_cached_independently(
        self,
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
        sample_statement_2: SchoolAccountStatement,
        fixed_school_id: SchoolId,
        fixed_school_id_2: SchoolId,
        cleanup_cache: None,
    ) -> None:
        """Test different schools are cached with separate keys."""
        await cache.set(sample_statement)
        await cache.set(sample_statement_2)

        result_1 = await cache.get(fixed_school_id)
        result_2 = await cache.get(fixed_school_id_2)

        assert result_1 is not None
        assert result_2 is not None
        assert result_1.school_name == "Integration Test School"
        assert result_2.school_name == "Second Test School"


# ============================================================================
# Data Integrity
# ============================================================================


class TestRedisSchoolAccountStatementCacheDataIntegrity:
    """Integration tests for data integrity after serialization round-trip."""

    async def test_all_fields_preserved(
        self,
        cache: RedisSchoolAccountStatementCache,
        sample_statement: SchoolAccountStatement,
        fixed_school_id: SchoolId,
        cleanup_cache: None,
    ) -> None:
        """Test all statement fields are preserved through cache round-trip."""
        await cache.set(sample_statement)

        result = await cache.get(fixed_school_id)

        assert result is not None
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

    async def test_decimal_precision_preserved(
        self,
        cache: RedisSchoolAccountStatementCache,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
        cleanup_cache: None,
    ) -> None:
        """Test Decimal precision is preserved through cache round-trip."""
        statement = SchoolAccountStatement(
            school_id=fixed_school_id,
            school_name="Precision Test",
            total_students=1,
            active_students=1,
            total_invoiced=Decimal("123456.78"),
            total_paid=Decimal("100000.00"),
            total_pending=Decimal("23456.78"),
            invoices_pending=1,
            invoices_partially_paid=0,
            invoices_paid=0,
            invoices_overdue=0,
            invoices_cancelled=0,
            total_late_fees=Decimal("0.01"),
            statement_date=fixed_time,
        )
        await cache.set(statement)

        result = await cache.get(fixed_school_id)

        assert result is not None
        assert result.total_invoiced == Decimal("123456.78")
        assert result.total_late_fees == Decimal("0.01")
        assert str(result.total_invoiced) == "123456.78"
        assert str(result.total_late_fees) == "0.01"

    async def test_datetime_timezone_preserved(
        self,
        cache: RedisSchoolAccountStatementCache,
        fixed_school_id: SchoolId,
        cleanup_cache: None,
    ) -> None:
        """Test datetime with UTC timezone is preserved through cache round-trip."""
        statement_date = datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC)
        statement = SchoolAccountStatement(
            school_id=fixed_school_id,
            school_name="Timezone Test",
            total_students=1,
            active_students=1,
            total_invoiced=Decimal("100.00"),
            total_paid=Decimal("0.00"),
            total_pending=Decimal("100.00"),
            invoices_pending=1,
            invoices_partially_paid=0,
            invoices_paid=0,
            invoices_overdue=0,
            invoices_cancelled=0,
            total_late_fees=Decimal("0.00"),
            statement_date=statement_date,
        )
        await cache.set(statement)

        result = await cache.get(fixed_school_id)

        assert result is not None
        assert result.statement_date == statement_date
        assert result.statement_date.tzinfo is not None


# ============================================================================
# TTL Behavior
# ============================================================================


class TestRedisSchoolAccountStatementCacheTTL:
    """Integration tests for TTL behavior."""

    async def test_cache_key_has_ttl(
        self,
        cache: RedisSchoolAccountStatementCache,
        redis_client: Redis,
        sample_statement: SchoolAccountStatement,
        fixed_school_id: SchoolId,
        cleanup_cache: None,
    ) -> None:
        """Test cached key has TTL set."""
        await cache.set(sample_statement)

        key = f"{RedisSchoolAccountStatementCache.KEY_PREFIX}:{fixed_school_id.value}"
        ttl = await redis_client.ttl(key)

        # TTL should be positive (key exists and has expiry)
        assert ttl > 0
        # TTL should be less than or equal to configured value (300s)
        assert ttl <= 300


# ============================================================================
# Key Format
# ============================================================================


class TestRedisSchoolAccountStatementCacheKeyFormat:
    """Integration tests for Redis key format."""

    async def test_key_format_in_redis(
        self,
        cache: RedisSchoolAccountStatementCache,
        redis_client: Redis,
        sample_statement: SchoolAccountStatement,
        fixed_school_id: SchoolId,
        cleanup_cache: None,
    ) -> None:
        """Test key stored in Redis matches expected format."""
        await cache.set(sample_statement)

        expected_key = (
            f"mattilda:cache:v1:account_statement:school:{fixed_school_id.value}"
        )
        exists = await redis_client.exists(expected_key)

        assert exists == 1

    async def test_key_contains_school_id(
        self,
        cache: RedisSchoolAccountStatementCache,
        redis_client: Redis,
        sample_statement: SchoolAccountStatement,
        fixed_school_id: SchoolId,
        cleanup_cache: None,
    ) -> None:
        """Test key contains the school ID."""
        await cache.set(sample_statement)

        pattern = f"*{fixed_school_id.value}*"
        keys = [key async for key in redis_client.scan_iter(match=pattern)]

        assert len(keys) == 1
        assert str(fixed_school_id.value) in keys[0]
