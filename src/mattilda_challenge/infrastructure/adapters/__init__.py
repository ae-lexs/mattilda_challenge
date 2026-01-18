"""Infrastructure adapters."""

from mattilda_challenge.infrastructure.adapters.invoice_repository import (
    InMemoryInvoiceRepository,
    PostgresInvoiceRepository,
)
from mattilda_challenge.infrastructure.adapters.payment_repository import (
    InMemoryPaymentRepository,
    PostgresPaymentRepository,
)
from mattilda_challenge.infrastructure.adapters.school_account_statement_cache import (
    NullSchoolAccountStatementCache,
    RedisSchoolAccountStatementCache,
)
from mattilda_challenge.infrastructure.adapters.school_repository import (
    InMemorySchoolRepository,
    PostgresSchoolRepository,
)
from mattilda_challenge.infrastructure.adapters.student_account_statement_cache import (
    NullStudentAccountStatementCache,
    RedisStudentAccountStatementCache,
)
from mattilda_challenge.infrastructure.adapters.student_repository import (
    InMemoryStudentRepository,
    PostgresStudentRepository,
)
from mattilda_challenge.infrastructure.adapters.time_provider import (
    FixedTimeProvider,
    SystemTimeProvider,
)

__all__ = [
    # Time Provider
    "FixedTimeProvider",
    "SystemTimeProvider",
    # Invoice Repository
    "InMemoryInvoiceRepository",
    "PostgresInvoiceRepository",
    # Payment Repository
    "InMemoryPaymentRepository",
    "PostgresPaymentRepository",
    # School Account Statement Cache
    "NullSchoolAccountStatementCache",
    "RedisSchoolAccountStatementCache",
    # School Repository
    "InMemorySchoolRepository",
    "PostgresSchoolRepository",
    # Student Account Statement Cache
    "NullStudentAccountStatementCache",
    "RedisStudentAccountStatementCache",
    # Student Repository
    "InMemoryStudentRepository",
    "PostgresStudentRepository",
]
