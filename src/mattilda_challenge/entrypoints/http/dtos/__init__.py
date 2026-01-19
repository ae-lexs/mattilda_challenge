"""Data Transfer Objects for HTTP layer."""

from mattilda_challenge.entrypoints.http.dtos.account_statement_dtos import (
    SchoolAccountStatementDTO,
    StudentAccountStatementDTO,
)
from mattilda_challenge.entrypoints.http.dtos.common_dtos import (
    ErrorResponseDTO,
    PaginatedResponseDTO,
)
from mattilda_challenge.entrypoints.http.dtos.health_dtos import (
    DependencyHealth,
    HealthResponse,
    HealthStatus,
    LivenessResponse,
)
from mattilda_challenge.entrypoints.http.dtos.invoice_dtos import (
    CancelInvoiceRequestDTO,
    InvoiceCreateRequestDTO,
    InvoiceResponseDTO,
)
from mattilda_challenge.entrypoints.http.dtos.payment_dtos import (
    PaymentCreateRequestDTO,
    PaymentResponseDTO,
)
from mattilda_challenge.entrypoints.http.dtos.school_dtos import (
    SchoolCreateRequestDTO,
    SchoolResponseDTO,
    SchoolUpdateRequestDTO,
)
from mattilda_challenge.entrypoints.http.dtos.student_dtos import (
    StudentCreateRequestDTO,
    StudentResponseDTO,
    StudentUpdateRequestDTO,
)

__all__ = [
    "CancelInvoiceRequestDTO",
    "DependencyHealth",
    "ErrorResponseDTO",
    "HealthResponse",
    "HealthStatus",
    "InvoiceCreateRequestDTO",
    "InvoiceResponseDTO",
    "LivenessResponse",
    "PaginatedResponseDTO",
    "PaymentCreateRequestDTO",
    "PaymentResponseDTO",
    "SchoolAccountStatementDTO",
    "SchoolCreateRequestDTO",
    "SchoolResponseDTO",
    "SchoolUpdateRequestDTO",
    "StudentAccountStatementDTO",
    "StudentCreateRequestDTO",
    "StudentResponseDTO",
    "StudentUpdateRequestDTO",
]
