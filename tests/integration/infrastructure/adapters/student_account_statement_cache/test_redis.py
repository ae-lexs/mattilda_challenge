"""Integration tests for RedisStudentAccountStatementCache.

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

from mattilda_challenge.application.dtos import StudentAccountStatement
from mattilda_challenge.domain.value_objects import StudentId
from mattilda_challenge.infrastructure.adapters.student_account_statement_cache import (
    RedisStudentAccountStatementCache,
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
async def cache(redis_client: Redis) -> RedisStudentAccountStatementCache:
    """Provide RedisStudentAccountStatementCache with real Redis."""
    # Patch settings for test TTL
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "mattilda_challenge.infrastructure.adapters.student_account_statement_cache.redis._settings.cache_ttl_seconds",
            300,
        )
        yield RedisStudentAccountStatementCache(redis_client)


@pytest.fixture
async def cleanup_cache(redis_client: Redis):
    """Clean up test keys before and after each test."""
    pattern = f"{RedisStudentAccountStatementCache.KEY_PREFIX}:*"

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
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def fixed_student_id_2() -> StudentId:
    """Provide second fixed student ID for testing."""
    return StudentId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def sample_statement(
    fixed_student_id: StudentId,
    fixed_time: datetime,
) -> StudentAccountStatement:
    """Provide sample student account statement for testing."""
    return StudentAccountStatement(
        student_id=fixed_student_id,
        student_name="Integration Test Student",
        school_name="Integration Test School",
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
def sample_statement_2(
    fixed_student_id_2: StudentId,
    fixed_time: datetime,
) -> StudentAccountStatement:
    """Provide second sample statement for testing."""
    return StudentAccountStatement(
        student_id=fixed_student_id_2,
        student_name="Second Test Student",
        school_name="Second Test School",
        total_invoiced=Decimal("2250.00"),
        total_paid=Decimal("1500.00"),
        total_pending=Decimal("750.00"),
        invoices_pending=2,
        invoices_partially_paid=0,
        invoices_paid=3,
        invoices_overdue=1,
        invoices_cancelled=0,
        total_late_fees=Decimal("62.75"),
        statement_date=fixed_time,
    )


# ============================================================================
# Basic Operations
# ============================================================================


class TestRedisStudentAccountStatementCacheSetGet:
    """Integration tests for set and get operations."""

    async def test_set_then_get_returns_statement(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
        fixed_student_id: StudentId,
        cleanup_cache: None,
    ) -> None:
        """Test set followed by get returns the cached statement."""
        await cache.set(sample_statement)

        result = await cache.get(fixed_student_id)

        assert result is not None
        assert result.student_id == fixed_student_id
        assert result.student_name == "Integration Test Student"

    async def test_get_returns_none_when_not_cached(
        self,
        cache: RedisStudentAccountStatementCache,
        fixed_student_id: StudentId,
        cleanup_cache: None,
    ) -> None:
        """Test get returns None when key doesn't exist."""
        result = await cache.get(fixed_student_id)

        assert result is None

    async def test_set_overwrites_existing_cache(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
        fixed_student_id: StudentId,
        fixed_time: datetime,
        cleanup_cache: None,
    ) -> None:
        """Test set overwrites previously cached statement."""
        await cache.set(sample_statement)

        updated_statement = StudentAccountStatement(
            student_id=fixed_student_id,
            student_name="Updated Student Name",
            school_name="Updated School Name",
            total_invoiced=Decimal("6000.00"),
            total_paid=Decimal("5000.00"),
            total_pending=Decimal("1000.00"),
            invoices_pending=2,
            invoices_partially_paid=1,
            invoices_paid=8,
            invoices_overdue=1,
            invoices_cancelled=2,
            total_late_fees=Decimal("200.00"),
            statement_date=fixed_time,
        )
        await cache.set(updated_statement)

        result = await cache.get(fixed_student_id)

        assert result is not None
        assert result.student_name == "Updated Student Name"
        assert result.total_invoiced == Decimal("6000.00")

    async def test_different_students_cached_independently(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
        sample_statement_2: StudentAccountStatement,
        fixed_student_id: StudentId,
        fixed_student_id_2: StudentId,
        cleanup_cache: None,
    ) -> None:
        """Test different students are cached with separate keys."""
        await cache.set(sample_statement)
        await cache.set(sample_statement_2)

        result_1 = await cache.get(fixed_student_id)
        result_2 = await cache.get(fixed_student_id_2)

        assert result_1 is not None
        assert result_2 is not None
        assert result_1.student_name == "Integration Test Student"
        assert result_2.student_name == "Second Test Student"


# ============================================================================
# Data Integrity
# ============================================================================


class TestRedisStudentAccountStatementCacheDataIntegrity:
    """Integration tests for data integrity after serialization round-trip."""

    async def test_all_fields_preserved(
        self,
        cache: RedisStudentAccountStatementCache,
        sample_statement: StudentAccountStatement,
        fixed_student_id: StudentId,
        cleanup_cache: None,
    ) -> None:
        """Test all statement fields are preserved through cache round-trip."""
        await cache.set(sample_statement)

        result = await cache.get(fixed_student_id)

        assert result is not None
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

    async def test_decimal_precision_preserved(
        self,
        cache: RedisStudentAccountStatementCache,
        fixed_student_id: StudentId,
        fixed_time: datetime,
        cleanup_cache: None,
    ) -> None:
        """Test Decimal precision is preserved through cache round-trip."""
        statement = StudentAccountStatement(
            student_id=fixed_student_id,
            student_name="Precision Test",
            school_name="Precision School",
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

        result = await cache.get(fixed_student_id)

        assert result is not None
        assert result.total_invoiced == Decimal("123456.78")
        assert result.total_late_fees == Decimal("0.01")
        assert str(result.total_invoiced) == "123456.78"
        assert str(result.total_late_fees) == "0.01"

    async def test_datetime_timezone_preserved(
        self,
        cache: RedisStudentAccountStatementCache,
        fixed_student_id: StudentId,
        cleanup_cache: None,
    ) -> None:
        """Test datetime with UTC timezone is preserved through cache round-trip."""
        statement_date = datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC)
        statement = StudentAccountStatement(
            student_id=fixed_student_id,
            student_name="Timezone Test",
            school_name="Timezone School",
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

        result = await cache.get(fixed_student_id)

        assert result is not None
        assert result.statement_date == statement_date
        assert result.statement_date.tzinfo is not None


# ============================================================================
# TTL Behavior
# ============================================================================


class TestRedisStudentAccountStatementCacheTTL:
    """Integration tests for TTL behavior."""

    async def test_cache_key_has_ttl(
        self,
        cache: RedisStudentAccountStatementCache,
        redis_client: Redis,
        sample_statement: StudentAccountStatement,
        fixed_student_id: StudentId,
        cleanup_cache: None,
    ) -> None:
        """Test cached key has TTL set."""
        await cache.set(sample_statement)

        key = f"{RedisStudentAccountStatementCache.KEY_PREFIX}:{fixed_student_id.value}"
        ttl = await redis_client.ttl(key)

        # TTL should be positive (key exists and has expiry)
        assert ttl > 0
        # TTL should be less than or equal to configured value (300s)
        assert ttl <= 300


# ============================================================================
# Key Format
# ============================================================================


class TestRedisStudentAccountStatementCacheKeyFormat:
    """Integration tests for Redis key format."""

    async def test_key_format_in_redis(
        self,
        cache: RedisStudentAccountStatementCache,
        redis_client: Redis,
        sample_statement: StudentAccountStatement,
        fixed_student_id: StudentId,
        cleanup_cache: None,
    ) -> None:
        """Test key stored in Redis matches expected format."""
        await cache.set(sample_statement)

        expected_key = (
            f"mattilda:cache:v1:account_statement:student:{fixed_student_id.value}"
        )
        exists = await redis_client.exists(expected_key)

        assert exists == 1

    async def test_key_contains_student_id(
        self,
        cache: RedisStudentAccountStatementCache,
        redis_client: Redis,
        sample_statement: StudentAccountStatement,
        fixed_student_id: StudentId,
        cleanup_cache: None,
    ) -> None:
        """Test key contains the student ID."""
        await cache.set(sample_statement)

        pattern = f"*{fixed_student_id.value}*"
        keys = [key async for key in redis_client.scan_iter(match=pattern)]

        assert len(keys) == 1
        assert str(fixed_student_id.value) in keys[0]
