"""Fixtures for integration tests.

These fixtures provide database session and test data setup for
integration tests that require a real PostgreSQL database.
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    SchoolId,
    StudentId,
)
from mattilda_challenge.infrastructure.adapters.invoice_repository import (
    PostgresInvoiceRepository,
)
from mattilda_challenge.infrastructure.postgres.models import (
    InvoiceModel,
    SchoolModel,
    StudentModel,
)

# Test database URL - uses main database with transaction rollback for isolation
# In Docker: db:5432, locally: localhost:5432
_db_host = os.getenv("DB_HOST", "db")
TEST_DATABASE_URL = f"postgresql+asyncpg://user:pass@{_db_host}:5432/mattilda"
TEST_DATABASE_URL_SYNC = f"postgresql://user:pass@{_db_host}:5432/mattilda"


@pytest.fixture
def engine() -> Generator[AsyncEngine]:
    """Create async engine for test database.

    Function-scoped to ensure each test gets a fresh engine in its own
    event loop, avoiding 'Future attached to different loop' errors.
    Uses NullPool to disable connection pooling.
    """
    eng = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable pooling - each test gets fresh connections
    )
    yield eng
    eng.sync_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def cleanup_database() -> Generator[None]:
    """
    Clean up test data at the start and end of the test session.

    Uses synchronous SQLAlchemy to avoid event loop issues with session-scoped
    async fixtures in pytest-asyncio.
    """
    sync_engine = create_engine(TEST_DATABASE_URL_SYNC)

    with sync_engine.connect() as conn:
        # Truncate all tables in correct order (respect foreign keys)
        conn.execute(text("TRUNCATE payments, invoices, students, schools CASCADE"))
        conn.commit()

    yield

    # Cleanup after all tests
    with sync_engine.connect() as conn:
        conn.execute(text("TRUNCATE payments, invoices, students, schools CASCADE"))
        conn.commit()

    sync_engine.dispose()


@pytest.fixture
async def db_session(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession]:
    """
    Provide database session for each test with proper transaction isolation.

    Uses connection-level transaction that is always rolled back at the end,
    ensuring complete test isolation. The session is bound directly to the
    connection's transaction.
    """
    # Get a connection and start a transaction at the connection level
    conn = await engine.connect()
    trans = await conn.begin()

    # Create session bound to this connection
    session = AsyncSession(bind=conn, expire_on_commit=False)

    try:
        yield session
    finally:
        # Close session first (doesn't affect the transaction)
        await session.close()
        # Rollback the connection-level transaction - this discards ALL changes
        await trans.rollback()
        # Close the connection
        await conn.close()


@pytest.fixture
def invoice_repository(db_session: AsyncSession) -> PostgresInvoiceRepository:
    """Provide PostgresInvoiceRepository instance."""
    return PostgresInvoiceRepository(db_session)


# ============================================================================
# Fixed Test Data - Explicit values for reproducibility (per CONTRIBUTING.md)
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
def fixed_school_id_2() -> SchoolId:
    """Provide second fixed school ID for cross-aggregate filter tests."""
    return SchoolId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))


@pytest.fixture
def fixed_student_id_2() -> StudentId:
    """Provide second fixed student ID for testing."""
    return StudentId(value=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))


@pytest.fixture
def fixed_invoice_id() -> InvoiceId:
    """Provide fixed invoice ID for testing."""
    return InvoiceId(value=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))


@pytest.fixture
def fixed_invoice_id_2() -> InvoiceId:
    """Provide second fixed invoice ID for testing."""
    return InvoiceId(value=UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"))


@pytest.fixture
def fixed_invoice_id_3() -> InvoiceId:
    """Provide third fixed invoice ID for pagination tests."""
    return InvoiceId(value=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"))


@pytest.fixture
def standard_late_fee_policy() -> LateFeePolicy:
    """Provide standard late fee policy for testing."""
    return LateFeePolicy(monthly_rate=Decimal("0.05"))


# ============================================================================
# Database Model Fixtures - Insert test data directly via ORM models
# ============================================================================


@pytest.fixture
async def saved_school(
    db_session: AsyncSession,
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> SchoolModel:
    """Insert a school into the test database."""
    school = SchoolModel(
        id=fixed_school_id.value,
        name="Test School",
        address="123 Test Street",
        created_at=fixed_time,
    )
    db_session.add(school)
    await db_session.flush()
    return school


@pytest.fixture
async def saved_school_2(
    db_session: AsyncSession,
    fixed_school_id_2: SchoolId,
    fixed_time: datetime,
) -> SchoolModel:
    """Insert a second school for cross-aggregate filter tests."""
    school = SchoolModel(
        id=fixed_school_id_2.value,
        name="Second School",
        address="456 Other Avenue",
        created_at=fixed_time,
    )
    db_session.add(school)
    await db_session.flush()
    return school


@pytest.fixture
async def saved_student(
    db_session: AsyncSession,
    saved_school: SchoolModel,
    fixed_student_id: StudentId,
    fixed_time: datetime,
) -> StudentModel:
    """Insert a student into the test database."""
    student = StudentModel(
        id=fixed_student_id.value,
        school_id=saved_school.id,
        first_name="John",
        last_name="Doe",
        email="john.doe@test.com",
        status="active",
        enrollment_date=fixed_time,
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    db_session.add(student)
    await db_session.flush()
    return student


@pytest.fixture
async def saved_student_2(
    db_session: AsyncSession,
    saved_school_2: SchoolModel,
    fixed_student_id_2: StudentId,
    fixed_time: datetime,
) -> StudentModel:
    """Insert a second student (different school) for cross-aggregate filter tests."""
    student = StudentModel(
        id=fixed_student_id_2.value,
        school_id=saved_school_2.id,
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@test.com",
        status="active",
        enrollment_date=fixed_time,
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    db_session.add(student)
    await db_session.flush()
    return student


@pytest.fixture
async def saved_invoice(
    db_session: AsyncSession,
    saved_student: StudentModel,
    fixed_invoice_id: InvoiceId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> InvoiceModel:
    """Insert an invoice into the test database."""
    invoice = InvoiceModel(
        id=fixed_invoice_id.value,
        student_id=saved_student.id,
        invoice_number="INV-2024-000001",
        amount=Decimal("1000.00"),
        due_date=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
        description="Tuition fee for January 2024",
        late_fee_policy_monthly_rate=standard_late_fee_policy.monthly_rate,
        status="pending",
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    db_session.add(invoice)
    await db_session.flush()
    return invoice


# ============================================================================
# Domain Entity Fixtures - For creating entities to save via repository
# ============================================================================


@pytest.fixture
def sample_invoice(
    fixed_invoice_id: InvoiceId,
    fixed_student_id: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Create a sample Invoice domain entity."""
    return Invoice(
        id=fixed_invoice_id,
        student_id=fixed_student_id,
        invoice_number="INV-2024-000001",
        amount=Decimal("1000.00"),
        due_date=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
        description="Tuition fee for January 2024",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PENDING,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def sample_invoice_2(
    fixed_invoice_id_2: InvoiceId,
    fixed_student_id: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Create a second sample Invoice domain entity."""
    return Invoice(
        id=fixed_invoice_id_2,
        student_id=fixed_student_id,
        invoice_number="INV-2024-000002",
        amount=Decimal("500.00"),
        due_date=datetime(2024, 3, 1, 0, 0, 0, tzinfo=UTC),
        description="Tuition fee for February 2024",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PENDING,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def sample_invoice_3(
    fixed_invoice_id_3: InvoiceId,
    fixed_student_id: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Create a third sample Invoice domain entity for pagination tests."""
    return Invoice(
        id=fixed_invoice_id_3,
        student_id=fixed_student_id,
        invoice_number="INV-2024-000003",
        amount=Decimal("750.00"),
        due_date=datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC),
        description="Tuition fee for March 2024",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PARTIALLY_PAID,
        created_at=fixed_time,
        updated_at=fixed_time,
    )
