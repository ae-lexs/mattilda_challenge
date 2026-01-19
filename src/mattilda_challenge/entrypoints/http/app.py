"""FastAPI application configuration.

Provides the FastAPI app factory with:
- Lifespan handler for startup/shutdown
- Global exception handlers for domain errors
- Middleware configuration (request ID)
- Route registration
- OpenAPI documentation
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from mattilda_challenge.config import get_settings
from mattilda_challenge.domain.exceptions import (
    CannotPayCancelledInvoiceError,
    DomainError,
    InvalidAmountError,
    InvalidIdError,
    InvalidInvoiceAmountError,
    InvalidInvoiceDataError,
    InvalidPaymentAmountError,
    InvalidPaymentDataError,
    InvalidSchoolDataError,
    InvalidStateTransitionError,
    InvalidStudentDataError,
    InvalidTimestampError,
    InvoiceNotFoundError,
    PaymentExceedsBalanceError,
    PaymentExceedsInvoiceAmountError,
    PaymentNotFoundError,
    SchoolNotFoundError,
    StudentNotFoundError,
)
from mattilda_challenge.entrypoints.http.routes import (
    health,
    invoices,
    payments,
    schools,
    students,
)
from mattilda_challenge.infrastructure.observability import (
    RequestIdMiddleware,
    configure_logging,
    get_logger,
    setup_metrics,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan handler."""
    settings = get_settings()

    # Configure logging
    configure_logging(debug=settings.debug)

    logger = get_logger(__name__)
    logger.info(
        "application_starting",
        version=settings.app_version,
        environment="development" if settings.debug else "production",
    )

    yield

    logger.info("application_shutting_down")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Mattilda Challenge API",
        description="""
School billing system API for managing schools, students, invoices, and payments.

## Features
- School and student management
- Invoice generation and tracking
- Payment recording with partial payment support
- Account statement generation (aggregated financial summaries)
- Late fee calculation for overdue invoices

## Financial Precision
All monetary values use exact decimal arithmetic (never floating point).
Amounts are represented as strings in API requests/responses to preserve precision.

## Identifiers
All entities use UUID-based identifiers for security and distributed generation.
UUIDs are represented as strings in API requests/responses.

## Timestamps
All timestamps use ISO 8601 format in UTC timezone (always ending with 'Z').
Example: `2024-01-15T10:30:00Z`

## Business Domain
- **Schools (Colegios)**: Educational institutions
- **Students (Estudiantes)**: Students enrolled in schools
- **Invoices (Facturas)**: Bills issued to students
- **Payments (Pagos)**: Monetary transactions against invoices

## Key Business Questions Answered
- ¿Cuánto le debe un estudiante a un colegio? → Student account statement
- ¿Cuánto le deben todos los estudiantes? → School account statement
- ¿Cuántos alumnos tiene un colegio? → School account statement
        """,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Add middleware (order matters: outermost first)
    app.add_middleware(RequestIdMiddleware)

    # Setup metrics
    if settings.enable_metrics:
        setup_metrics(app)

    # Register exception handlers
    _register_exception_handlers(app)

    # Register routes
    app.include_router(health.router)
    app.include_router(schools.router, prefix="/api/v1", tags=["Schools"])
    app.include_router(students.router, prefix="/api/v1", tags=["Students"])
    app.include_router(invoices.router, prefix="/api/v1", tags=["Invoices"])
    app.include_router(payments.router, prefix="/api/v1", tags=["Payments"])

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for domain errors."""

    # 404 Not Found errors
    @app.exception_handler(SchoolNotFoundError)
    @app.exception_handler(StudentNotFoundError)
    @app.exception_handler(InvoiceNotFoundError)
    @app.exception_handler(PaymentNotFoundError)
    async def handle_not_found(request: Request, exc: DomainError) -> JSONResponse:
        """Handle resource not found errors."""
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    # 422 Validation errors (malformed/invalid input values)
    @app.exception_handler(InvalidInvoiceAmountError)
    @app.exception_handler(InvalidPaymentAmountError)
    @app.exception_handler(InvalidInvoiceDataError)
    @app.exception_handler(InvalidPaymentDataError)
    @app.exception_handler(InvalidStudentDataError)
    @app.exception_handler(InvalidSchoolDataError)
    @app.exception_handler(InvalidTimestampError)
    @app.exception_handler(InvalidAmountError)
    @app.exception_handler(InvalidIdError)
    async def handle_validation_error(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        """Handle input validation errors."""
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    # 400 Business rule violations (valid input, violates domain constraints)
    @app.exception_handler(InvalidStateTransitionError)
    @app.exception_handler(CannotPayCancelledInvoiceError)
    @app.exception_handler(PaymentExceedsBalanceError)
    @app.exception_handler(PaymentExceedsInvoiceAmountError)
    async def handle_business_rule_violation(
        request: Request, exc: DomainError
    ) -> JSONResponse:
        """Handle business rule violations."""
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    # 500 Unexpected errors (catch-all)
    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unexpected errors."""
        logger = get_logger(__name__)
        logger.error(
            "unexpected_error",
            error_type=type(exc).__name__,
            message=str(exc),
            path=request.url.path,
            exc_info=True,
        )

        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}
        )


# Create the app instance for uvicorn
app = create_app()
