"""Redis implementation of SchoolAccountStatementCache port.

This module provides the Redis-backed cache adapter for school account statements.
It implements the fail-open pattern where cache errors return None rather than
raising exceptions, ensuring the system continues operating via database fallback.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from redis.asyncio import Redis
from redis.exceptions import RedisError

from mattilda_challenge.application.dtos import SchoolAccountStatement
from mattilda_challenge.application.ports import SchoolAccountStatementCache
from mattilda_challenge.config import get_settings
from mattilda_challenge.domain.exceptions import InvalidSchoolIdError
from mattilda_challenge.domain.value_objects import SchoolId

logger = logging.getLogger(__name__)


class RedisSchoolAccountStatementCache(SchoolAccountStatementCache):
    """
    Redis implementation of SchoolAccountStatementCache port.

    Same pattern as RedisStudentAccountStatementCache.
    """

    KEY_PREFIX = "mattilda:cache:v1:account_statement:school"

    def __init__(self, redis_client: Redis):
        self._redis = redis_client
        self._ttl = get_settings().cache_ttl_seconds

    async def get(self, school_id: SchoolId) -> SchoolAccountStatement | None:
        """Retrieve cached school account statement."""
        key = self._build_key(school_id)

        try:
            cached = await self._redis.get(key)

            if cached is None:
                logger.debug("cache_miss key=%s", key)
                return None

            logger.debug("cache_hit key=%s", key)
            return self._deserialize(cached)

        except RedisError as e:
            logger.warning(
                "cache_error_on_get key=%s error=%s error_type=%s",
                key,
                str(e),
                type(e).__name__,
            )
            return None
        except (
            json.JSONDecodeError,
            KeyError,
            ValueError,
            InvalidSchoolIdError,
            InvalidOperation,
        ) as e:
            logger.warning(
                "cache_deserialization_error key=%s error=%s",
                key,
                str(e),
            )
            return None

    async def set(self, statement: SchoolAccountStatement) -> None:
        """Cache school account statement with TTL."""
        key = self._build_key(statement.school_id)

        try:
            serialized = self._serialize(statement)
            await self._redis.set(key, serialized, ex=self._ttl)
            logger.debug("cache_set key=%s ttl=%s", key, self._ttl)

        except RedisError as e:
            logger.warning(
                "cache_error_on_set key=%s error=%s error_type=%s",
                key,
                str(e),
                type(e).__name__,
            )

    def _build_key(self, school_id: SchoolId) -> str:
        """Build Redis key for school account statement."""
        return f"{self.KEY_PREFIX}:{school_id.value}"

    def _serialize(self, statement: SchoolAccountStatement) -> str:
        """Serialize account statement to JSON string."""
        return json.dumps(
            {
                "school_id": str(statement.school_id.value),
                "school_name": statement.school_name,
                "total_students": statement.total_students,
                "active_students": statement.active_students,
                "total_invoiced": str(statement.total_invoiced),
                "total_paid": str(statement.total_paid),
                "total_pending": str(statement.total_pending),
                "invoices_pending": statement.invoices_pending,
                "invoices_partially_paid": statement.invoices_partially_paid,
                "invoices_paid": statement.invoices_paid,
                "invoices_overdue": statement.invoices_overdue,
                "invoices_cancelled": statement.invoices_cancelled,
                "total_late_fees": str(statement.total_late_fees),
                "statement_date": statement.statement_date.isoformat(),
            }
        )

    def _deserialize(self, json_str: str) -> SchoolAccountStatement:
        """Deserialize JSON string to account statement."""
        data = json.loads(json_str)

        return SchoolAccountStatement(
            school_id=SchoolId.from_string(data["school_id"]),
            school_name=data["school_name"],
            total_students=data["total_students"],
            active_students=data["active_students"],
            total_invoiced=Decimal(data["total_invoiced"]),
            total_paid=Decimal(data["total_paid"]),
            total_pending=Decimal(data["total_pending"]),
            invoices_pending=data["invoices_pending"],
            invoices_partially_paid=data["invoices_partially_paid"],
            invoices_paid=data["invoices_paid"],
            invoices_overdue=data["invoices_overdue"],
            invoices_cancelled=data["invoices_cancelled"],
            total_late_fees=Decimal(data["total_late_fees"]),
            statement_date=datetime.fromisoformat(data["statement_date"]),
        )
