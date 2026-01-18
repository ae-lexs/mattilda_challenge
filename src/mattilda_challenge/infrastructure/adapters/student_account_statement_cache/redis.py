from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from redis.asyncio import Redis
from redis.exceptions import RedisError

from mattilda_challenge.application.dtos import StudentAccountStatement
from mattilda_challenge.application.ports import StudentAccountStatementCache
from mattilda_challenge.config import get_settings
from mattilda_challenge.domain.exceptions import InvalidStudentIdError
from mattilda_challenge.domain.value_objects import StudentId

logger = logging.getLogger(__name__)
_settings = get_settings()


class RedisStudentAccountStatementCache(StudentAccountStatementCache):
    """
    Redis implementation of StudentAccountStatementCache port.

    Uses JSON serialization with string decimals for precision.
    Implements fail-open pattern: errors return None, not exceptions.
    """

    KEY_PREFIX = "mattilda:cache:v1:account_statement:student"

    def __init__(self, redis_client: Redis):
        self._redis = redis_client
        self._ttl = _settings.cache_ttl_seconds

    async def get(self, student_id: StudentId) -> StudentAccountStatement | None:
        """Retrieve cached student account statement."""
        key = self._build_key(student_id)

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
            InvalidStudentIdError,
            InvalidOperation,
        ) as e:
            logger.warning(
                "cache_deserialization_error key=%s error=%s",
                key,
                str(e),
            )
            return None

    async def set(self, statement: StudentAccountStatement) -> None:
        """Cache student account statement with TTL."""
        key = self._build_key(statement.student_id)

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

    def _build_key(self, student_id: StudentId) -> str:
        """Build Redis key for student account statement."""
        return f"{self.KEY_PREFIX}:{student_id.value}"

    def _serialize(self, statement: StudentAccountStatement) -> str:
        """Serialize account statement to JSON string."""
        return json.dumps(
            {
                "student_id": str(statement.student_id.value),
                "student_name": statement.student_name,
                "school_name": statement.school_name,
                "total_invoiced": str(statement.total_invoiced),
                "total_paid": str(statement.total_paid),
                "total_pending": str(statement.total_pending),
                "invoices_pending": statement.invoices_pending,
                "invoices_partially_paid": statement.invoices_partially_paid,
                "invoices_paid": statement.invoices_paid,
                "invoices_cancelled": statement.invoices_cancelled,
                "invoices_overdue": statement.invoices_overdue,
                "total_late_fees": str(statement.total_late_fees),
                "statement_date": statement.statement_date.isoformat(),
            }
        )

    def _deserialize(self, json_str: str) -> StudentAccountStatement:
        """Deserialize JSON string to account statement."""
        data = json.loads(json_str)

        return StudentAccountStatement(
            student_id=StudentId.from_string(data["student_id"]),
            student_name=data["student_name"],
            school_name=data["school_name"],
            total_invoiced=Decimal(data["total_invoiced"]),
            total_paid=Decimal(data["total_paid"]),
            total_pending=Decimal(data["total_pending"]),
            invoices_pending=data["invoices_pending"],
            invoices_partially_paid=data["invoices_partially_paid"],
            invoices_paid=data["invoices_paid"],
            invoices_cancelled=data["invoices_cancelled"],
            invoices_overdue=data["invoices_overdue"],
            total_late_fees=Decimal(data["total_late_fees"]),
            statement_date=datetime.fromisoformat(data["statement_date"]),
        )
