"""Integration tests for PostgresPaymentRepository.

These tests verify the PostgreSQL repository implementation against
a real database. They test SQL query correctness and database interactions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import PaymentFilters
from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId, StudentId
from mattilda_challenge.infrastructure.adapters.payment_repository import (
    PostgresPaymentRepository,
)
from mattilda_challenge.infrastructure.postgres.models import (
    InvoiceModel,
    PaymentModel,
    SchoolModel,
    StudentModel,
)

pytestmark = pytest.mark.integration


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def payment_repository(db_session: AsyncSession) -> PostgresPaymentRepository:
    """Provide PostgresPaymentRepository instance."""
    return PostgresPaymentRepository(db_session)


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_school_id() -> UUID:
    """Provide fixed school ID for testing."""
    return UUID("11111111-1111-1111-1111-111111111111")


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
def fixed_payment_id() -> PaymentId:
    """Provide fixed payment ID for testing."""
    return PaymentId(value=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"))


@pytest.fixture
def fixed_payment_id_2() -> PaymentId:
    """Provide second fixed payment ID for testing."""
    return PaymentId(value=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"))


@pytest.fixture
def fixed_payment_id_3() -> PaymentId:
    """Provide third fixed payment ID for testing."""
    return PaymentId(value=UUID("00000000-0000-0000-0000-000000000001"))


@pytest.fixture
async def saved_school(
    db_session: AsyncSession,
    fixed_school_id: UUID,
    fixed_time: datetime,
) -> SchoolModel:
    """Insert a school into the test database."""
    school = SchoolModel(
        id=fixed_school_id,
        name="Test School",
        address="123 Test Street",
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
        email="john.doe@example.com",
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
    saved_school: SchoolModel,
    fixed_student_id_2: StudentId,
    fixed_time: datetime,
) -> StudentModel:
    """Insert second student into the test database."""
    student = StudentModel(
        id=fixed_student_id_2.value,
        school_id=saved_school.id,
        first_name="Jane",
        last_name="Smith",
        email="jane.smith@example.com",
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
) -> InvoiceModel:
    """Insert an invoice into the test database."""
    invoice = InvoiceModel(
        id=fixed_invoice_id.value,
        student_id=saved_student.id,
        invoice_number="INV-2024-000001",
        amount=Decimal("1000.00"),
        due_date=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
        description="Tuition fee",
        late_fee_policy_monthly_rate=Decimal("0.05"),
        status="pending",
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    db_session.add(invoice)
    await db_session.flush()
    return invoice


@pytest.fixture
async def saved_invoice_2(
    db_session: AsyncSession,
    saved_student_2: StudentModel,
    fixed_invoice_id_2: InvoiceId,
    fixed_time: datetime,
) -> InvoiceModel:
    """Insert second invoice (different student) into the test database."""
    invoice = InvoiceModel(
        id=fixed_invoice_id_2.value,
        student_id=saved_student_2.id,
        invoice_number="INV-2024-000002",
        amount=Decimal("500.00"),
        due_date=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
        description="Activity fee",
        late_fee_policy_monthly_rate=Decimal("0.05"),
        status="pending",
        created_at=fixed_time,
        updated_at=fixed_time,
    )
    db_session.add(invoice)
    await db_session.flush()
    return invoice


@pytest.fixture
async def saved_payment(
    db_session: AsyncSession,
    saved_invoice: InvoiceModel,
    fixed_payment_id: PaymentId,
    fixed_time: datetime,
) -> PaymentModel:
    """Insert a payment into the test database."""
    payment = PaymentModel(
        id=fixed_payment_id.value,
        invoice_id=saved_invoice.id,
        amount=Decimal("500.00"),
        payment_date=fixed_time,
        payment_method="bank_transfer",
        reference_number="REF-001",
        created_at=fixed_time,
    )
    db_session.add(payment)
    await db_session.flush()
    return payment


@pytest.fixture
async def saved_payment_2(
    db_session: AsyncSession,
    saved_invoice: InvoiceModel,
    fixed_payment_id_2: PaymentId,
) -> PaymentModel:
    """Insert second payment (same invoice) into the test database."""
    payment = PaymentModel(
        id=fixed_payment_id_2.value,
        invoice_id=saved_invoice.id,
        amount=Decimal("300.00"),
        payment_date=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
        payment_method="cash",
        reference_number=None,
        created_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
    )
    db_session.add(payment)
    await db_session.flush()
    return payment


@pytest.fixture
async def saved_payment_3(
    db_session: AsyncSession,
    saved_invoice_2: InvoiceModel,
    fixed_payment_id_3: PaymentId,
) -> PaymentModel:
    """Insert third payment (different invoice) into the test database."""
    payment = PaymentModel(
        id=fixed_payment_id_3.value,
        invoice_id=saved_invoice_2.id,
        amount=Decimal("250.00"),
        payment_date=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
        payment_method="card",
        reference_number="REF-003",
        created_at=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
    )
    db_session.add(payment)
    await db_session.flush()
    return payment


@pytest.fixture
def sample_payment(
    fixed_payment_id: PaymentId,
    fixed_invoice_id: InvoiceId,
    fixed_time: datetime,
) -> Payment:
    """Create a sample Payment domain entity."""
    return Payment(
        id=fixed_payment_id,
        invoice_id=fixed_invoice_id,
        amount=Decimal("500.00"),
        payment_date=fixed_time,
        payment_method="bank_transfer",
        reference_number="REF-001",
        created_at=fixed_time,
    )


# ============================================================================
# get_by_id Tests
# ============================================================================


class TestPostgresPaymentRepositoryGetById:
    """Tests for get_by_id method."""

    async def test_returns_payment_when_exists(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        fixed_payment_id: PaymentId,
    ) -> None:
        """Test get_by_id returns payment when it exists."""
        result = await payment_repository.get_by_id(fixed_payment_id)

        assert result is not None
        assert result.id == fixed_payment_id
        assert result.amount == Decimal("500.00")

    async def test_returns_none_when_not_found(
        self,
        payment_repository: PostgresPaymentRepository,
    ) -> None:
        """Test get_by_id returns None when payment doesn't exist."""
        non_existent_id = PaymentId(value=UUID("99999999-9999-9999-9999-999999999999"))

        result = await payment_repository.get_by_id(non_existent_id)

        assert result is None

    async def test_returns_correct_entity_fields(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        fixed_payment_id: PaymentId,
        fixed_invoice_id: InvoiceId,
    ) -> None:
        """Test get_by_id returns entity with all fields correctly mapped."""
        result = await payment_repository.get_by_id(fixed_payment_id)

        assert result is not None
        assert isinstance(result, Payment)
        assert result.invoice_id == fixed_invoice_id
        assert result.amount == Decimal("500.00")
        assert result.payment_method == "bank_transfer"
        assert result.reference_number == "REF-001"


# ============================================================================
# save Tests
# ============================================================================


class TestPostgresPaymentRepositorySave:
    """Tests for save method."""

    async def test_save_inserts_new_payment(
        self,
        payment_repository: PostgresPaymentRepository,
        sample_payment: Payment,
        saved_invoice: InvoiceModel,
    ) -> None:
        """Test save inserts new payment into database."""
        result = await payment_repository.save(sample_payment)

        assert result.id == sample_payment.id
        assert result.amount == sample_payment.amount

        # Verify it was persisted
        fetched = await payment_repository.get_by_id(sample_payment.id)
        assert fetched is not None

    async def test_save_preserves_decimal_precision(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_invoice: InvoiceModel,
        fixed_invoice_id: InvoiceId,
        fixed_time: datetime,
    ) -> None:
        """Test save preserves decimal precision."""
        payment = Payment(
            id=PaymentId.generate(),
            invoice_id=fixed_invoice_id,
            amount=Decimal("123.45"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
            reference_number=None,
            created_at=fixed_time,
        )

        result = await payment_repository.save(payment)

        assert result.amount == Decimal("123.45")
        assert isinstance(result.amount, Decimal)


# ============================================================================
# get_total_by_invoice Tests
# ============================================================================


class TestPostgresPaymentRepositoryGetTotalByInvoice:
    """Tests for get_total_by_invoice method."""

    async def test_returns_sum_of_payment_amounts(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
        fixed_invoice_id: InvoiceId,
    ) -> None:
        """Test get_total_by_invoice returns correct sum."""
        result = await payment_repository.get_total_by_invoice(fixed_invoice_id)

        # payment_1: 500.00, payment_2: 300.00
        assert result == Decimal("800.00")
        assert isinstance(result, Decimal)

    async def test_returns_zero_for_invoice_with_no_payments(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_invoice: InvoiceModel,
    ) -> None:
        """Test get_total_by_invoice returns 0 when no payments."""
        no_payment_invoice = InvoiceId(
            value=UUID("88888888-8888-8888-8888-888888888888")
        )

        result = await payment_repository.get_total_by_invoice(no_payment_invoice)

        assert result == Decimal("0")


# ============================================================================
# get_total_by_student Tests
# ============================================================================


class TestPostgresPaymentRepositoryGetTotalByStudent:
    """Tests for get_total_by_student method."""

    async def test_returns_sum_for_student(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
        fixed_student_id: StudentId,
    ) -> None:
        """Test get_total_by_student returns correct sum across invoices."""
        result = await payment_repository.get_total_by_student(fixed_student_id)

        # Student 1 has payments on invoice_1: 500 + 300 = 800
        assert result == Decimal("800.00")
        assert isinstance(result, Decimal)

    async def test_returns_zero_for_student_with_no_payments(
        self,
        payment_repository: PostgresPaymentRepository,
    ) -> None:
        """Test get_total_by_student returns 0 for no payments."""
        no_payment_student = StudentId(
            value=UUID("88888888-8888-8888-8888-888888888888")
        )

        result = await payment_repository.get_total_by_student(no_payment_student)

        assert result == Decimal("0")


# ============================================================================
# find_by_invoice Tests
# ============================================================================


class TestPostgresPaymentRepositoryFindByInvoice:
    """Tests for find_by_invoice method."""

    async def test_returns_invoice_payments(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
        fixed_invoice_id: InvoiceId,
    ) -> None:
        """Test find_by_invoice returns only payments for specified invoice."""
        result = await payment_repository.find_by_invoice(
            invoice_id=fixed_invoice_id,
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 2
        for payment in result.items:
            assert payment.invoice_id == fixed_invoice_id

    async def test_returns_empty_for_no_payments(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_invoice: InvoiceModel,
    ) -> None:
        """Test find_by_invoice returns empty for invoice with no payments."""
        no_payment_invoice = InvoiceId(
            value=UUID("99999999-9999-9999-9999-999999999999")
        )

        result = await payment_repository.find_by_invoice(
            invoice_id=no_payment_invoice,
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 0
        assert len(result.items) == 0


# ============================================================================
# find Tests - Filtering
# ============================================================================


class TestPostgresPaymentRepositoryFind:
    """Tests for find method."""

    async def test_find_returns_all_payments_without_filters(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
    ) -> None:
        """Test find returns all payments when no filters applied."""
        result = await payment_repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 3

    async def test_find_filters_by_invoice_id(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
        fixed_invoice_id: InvoiceId,
    ) -> None:
        """Test find filters by invoice_id correctly."""
        result = await payment_repository.find(
            filters=PaymentFilters(invoice_id=fixed_invoice_id.value),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 2
        for payment in result.items:
            assert payment.invoice_id == fixed_invoice_id

    async def test_find_filters_by_payment_date_range(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
    ) -> None:
        """Test find filters by payment date range correctly."""
        result = await payment_repository.find(
            filters=PaymentFilters(
                payment_date_from=datetime(2024, 1, 16, 0, 0, 0, tzinfo=UTC),
                payment_date_to=datetime(2024, 1, 16, 23, 59, 59, tzinfo=UTC),
            ),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="payment_date", sort_order="asc"),
        )

        # Only payment_2 (2024-01-16) falls in range
        assert result.total == 1


# ============================================================================
# find Tests - Pagination
# ============================================================================


class TestPostgresPaymentRepositoryFindPagination:
    """Tests for find method pagination."""

    async def test_find_respects_offset(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
    ) -> None:
        """Test find respects pagination offset."""
        result = await payment_repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=1, limit=10),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.offset == 1

    async def test_find_respects_limit(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
    ) -> None:
        """Test find respects pagination limit."""
        result = await payment_repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=2),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.limit == 2

    async def test_find_returns_correct_total(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
    ) -> None:
        """Test find returns correct total count regardless of pagination."""
        result = await payment_repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=1),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 1


# ============================================================================
# find Tests - Sorting
# ============================================================================


class TestPostgresPaymentRepositoryFindSorting:
    """Tests for find method sorting."""

    async def test_find_sorts_by_amount_ascending(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
    ) -> None:
        """Test find sorts by amount ascending."""
        result = await payment_repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        amounts = [p.amount for p in result.items]
        assert amounts == [Decimal("250.00"), Decimal("300.00"), Decimal("500.00")]

    async def test_find_sorts_by_payment_date_descending(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
        saved_payment_2: PaymentModel,
        saved_payment_3: PaymentModel,
    ) -> None:
        """Test find sorts by payment_date descending."""
        result = await payment_repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="payment_date", sort_order="desc"),
        )

        dates = [p.payment_date for p in result.items]
        assert dates == sorted(dates, reverse=True)

    async def test_find_returns_page_object(
        self,
        payment_repository: PostgresPaymentRepository,
        saved_payment: PaymentModel,
    ) -> None:
        """Test find returns Page object with correct structure."""
        result = await payment_repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert isinstance(result, Page)
        assert isinstance(result.items, tuple)
        assert result.offset == 0
        assert result.limit == 10
