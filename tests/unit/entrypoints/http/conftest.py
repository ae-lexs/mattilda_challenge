"""Fixtures for HTTP entrypoints tests.

Provides TestClient setup and mock dependencies for endpoint testing.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mattilda_challenge.application.common import Page
from mattilda_challenge.application.ports.time_provider import TimeProvider
from mattilda_challenge.application.ports.unit_of_work import UnitOfWork
from mattilda_challenge.domain.entities import Invoice, Payment, School, Student
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    PaymentId,
    SchoolId,
    StudentId,
    StudentStatus,
)
from mattilda_challenge.entrypoints.http.app import create_app
from mattilda_challenge.entrypoints.http.dependencies import (
    get_db_session,
    get_redis,
    get_school_account_statement_cache,
    get_student_account_statement_cache,
    get_time_provider,
    get_unit_of_work,
)

# ============================================================================
# Fixed Test Data
# ============================================================================


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_school_id() -> SchoolId:
    """Provide fixed school ID for testing."""
    return SchoolId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def fixed_invoice_id() -> InvoiceId:
    """Provide fixed invoice ID for testing."""
    return InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333"))


@pytest.fixture
def fixed_payment_id() -> PaymentId:
    """Provide fixed payment ID for testing."""
    return PaymentId(value=UUID("44444444-4444-4444-4444-444444444444"))


@pytest.fixture
def standard_late_fee_policy() -> LateFeePolicy:
    """Provide standard late fee policy for testing."""
    return LateFeePolicy(monthly_rate=Decimal("0.05"))


# ============================================================================
# Sample Entities
# ============================================================================


@pytest.fixture
def sample_school(fixed_school_id: SchoolId, fixed_time: datetime) -> School:
    """Provide sample school entity for testing."""
    return School(
        id=fixed_school_id,
        name="Test School",
        address="123 Test Street",
        created_at=fixed_time,
    )


@pytest.fixture
def sample_student(
    fixed_student_id: StudentId,
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> Student:
    """Provide sample student entity for testing."""
    return Student(
        id=fixed_student_id,
        school_id=fixed_school_id,
        first_name="John",
        last_name="Doe",
        email="john.doe@test.com",
        enrollment_date=fixed_time,
        status=StudentStatus.ACTIVE,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def sample_invoice(
    fixed_invoice_id: InvoiceId,
    fixed_student_id: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Provide sample invoice entity for testing."""
    due_date = datetime(2024, 2, 15, 0, 0, 0, tzinfo=UTC)
    return Invoice(
        id=fixed_invoice_id,
        student_id=fixed_student_id,
        invoice_number="INV-2024-000001",
        amount=Decimal("1500.00"),
        due_date=due_date,
        description="January 2024 Tuition",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PENDING,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def sample_payment(
    fixed_payment_id: PaymentId,
    fixed_invoice_id: InvoiceId,
    fixed_time: datetime,
) -> Payment:
    """Provide sample payment entity for testing."""
    return Payment(
        id=fixed_payment_id,
        invoice_id=fixed_invoice_id,
        amount=Decimal("500.00"),
        payment_date=fixed_time,
        payment_method="transfer",
        reference_number="REF-001",
        created_at=fixed_time,
    )


# ============================================================================
# Mock Dependencies
# ============================================================================


@pytest.fixture
def mock_time_provider(fixed_time: datetime) -> TimeProvider:
    """Provide mock time provider returning fixed time."""
    provider = MagicMock(spec=TimeProvider)
    provider.now.return_value = fixed_time
    return provider


@pytest.fixture
def mock_uow() -> UnitOfWork:
    """Provide mock unit of work with mocked repositories."""
    uow = AsyncMock(spec=UnitOfWork)
    uow.schools = AsyncMock()
    uow.students = AsyncMock()
    uow.invoices = AsyncMock()
    uow.payments = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def mock_student_cache() -> Any:
    """Provide mock student account statement cache."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_school_cache() -> Any:
    """Provide mock school account statement cache."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Provide mock Redis client."""
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_session() -> AsyncMock:
    """Provide mock database session."""
    return AsyncMock()


# ============================================================================
# TestClient Setup
# ============================================================================


@pytest.fixture
def app(
    mock_uow: UnitOfWork,
    mock_time_provider: TimeProvider,
    mock_student_cache: Any,
    mock_school_cache: Any,
    mock_redis: AsyncMock,
    mock_session: AsyncMock,
) -> FastAPI:
    """Create FastAPI app with mocked dependencies."""
    application = create_app()

    # Override dependencies
    application.dependency_overrides[get_unit_of_work] = lambda: mock_uow
    application.dependency_overrides[get_time_provider] = lambda: mock_time_provider
    application.dependency_overrides[get_student_account_statement_cache] = (
        lambda: mock_student_cache
    )
    application.dependency_overrides[get_school_account_statement_cache] = (
        lambda: mock_school_cache
    )
    application.dependency_overrides[get_redis] = lambda: mock_redis
    application.dependency_overrides[get_db_session] = lambda: mock_session

    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Provide TestClient for endpoint testing."""
    return TestClient(app, raise_server_exceptions=False)


# ============================================================================
# Helper Functions for Tests
# ============================================================================


def create_empty_page[T]() -> Page[T]:
    """Create empty paginated response."""
    return Page(items=[], total=0, offset=0, limit=20)


def create_page[T](items: list[T], total: int | None = None) -> Page[T]:
    """Create paginated response with items."""
    return Page(
        items=items,
        total=total if total is not None else len(items),
        offset=0,
        limit=20,
    )
