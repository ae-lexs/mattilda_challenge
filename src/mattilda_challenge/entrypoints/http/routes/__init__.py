"""HTTP route handlers."""

from mattilda_challenge.entrypoints.http.routes import (
    health,
    invoices,
    payments,
    schools,
    students,
)

__all__ = [
    "health",
    "invoices",
    "payments",
    "schools",
    "students",
]
