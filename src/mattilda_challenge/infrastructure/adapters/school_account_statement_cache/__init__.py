"""School cache adapter implementations."""

from mattilda_challenge.infrastructure.adapters.school_account_statement_cache.null import (
    NullSchoolAccountStatementCache,
)
from mattilda_challenge.infrastructure.adapters.school_account_statement_cache.redis import (
    RedisSchoolAccountStatementCache,
)

__all__ = [
    "NullSchoolAccountStatementCache",
    "RedisSchoolAccountStatementCache",
]
