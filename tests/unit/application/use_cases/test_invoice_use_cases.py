"""Unit tests for Invoice use cases.

Tests for CreateInvoiceUseCase, CancelInvoiceUseCase, and ListInvoicesUseCase
following the Arrange-Act-Assert pattern.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from mattilda_challenge.application.common import PaginationParams, SortParams
from mattilda_challenge.application.filters import InvoiceFilters
from mattilda_challenge.application.use_cases import (
    CancelInvoiceUseCase,
    CreateInvoiceUseCase,
    ListInvoicesUseCase,
)
from mattilda_challenge.application.use_cases.requests import (
    CancelInvoiceRequest,
    CreateInvoiceRequest,
)
from mattilda_challenge.domain.entities import Invoice, School, Student
from mattilda_challenge.domain.exceptions import (
    InvalidStateTransitionError,
    InvoiceNotFoundError,
    StudentNotFoundError,
)
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    SchoolId,
    StudentId,
)
from mattilda_challenge.infrastructure.adapters import InMemoryUnitOfWork

# ============================================================================
# Fixtures
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
def standard_late_fee_policy() -> LateFeePolicy:
    """Provide standard late fee policy for testing."""
    return LateFeePolicy(monthly_rate=Decimal("0.05"))


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
    return Student.create(
        school_id=fixed_school_id,
        first_name="John",
        last_name="Doe",
        email="john.doe@test.com",
        now=fixed_time,
    )


@pytest.fixture
def sample_invoice(
    fixed_invoice_id: InvoiceId,
    fixed_student_id: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Provide sample invoice entity for testing."""
    return Invoice(
        id=fixed_invoice_id,
        student_id=fixed_student_id,
        invoice_number="INV-2024-000001",
        amount=Decimal("1000.00"),
        due_date=datetime(2024, 2, 15, tzinfo=UTC),
        description="Test Invoice",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PENDING,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def uow() -> InMemoryUnitOfWork:
    """Provide fresh InMemoryUnitOfWork for each test."""
    return InMemoryUnitOfWork()


# ============================================================================
# CreateInvoiceUseCase
# ============================================================================


class TestCreateInvoiceUseCase:
    """Tests for CreateInvoiceUseCase."""

    async def test_execute_creates_invoice_with_correct_amount(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates invoice with the provided amount."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = CreateInvoiceUseCase()
        request = CreateInvoiceRequest(
            student_id=sample_student.id,
            amount=Decimal("1500.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Tuition Fee",
            late_fee_policy=standard_late_fee_policy,
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.amount == Decimal("1500.00")

    async def test_execute_creates_invoice_with_correct_student_id(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates invoice linked to the correct student."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = CreateInvoiceUseCase()
        request = CreateInvoiceRequest(
            student_id=sample_student.id,
            amount=Decimal("1500.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Tuition Fee",
            late_fee_policy=standard_late_fee_policy,
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.student_id == sample_student.id

    async def test_execute_creates_invoice_with_pending_status(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates invoice with PENDING status by default."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = CreateInvoiceUseCase()
        request = CreateInvoiceRequest(
            student_id=sample_student.id,
            amount=Decimal("1500.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Tuition Fee",
            late_fee_policy=standard_late_fee_policy,
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.status == InvoiceStatus.PENDING

    async def test_execute_creates_invoice_with_correct_due_date(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates invoice with the provided due date."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = CreateInvoiceUseCase()
        due_date = datetime(2024, 3, 1, tzinfo=UTC)
        request = CreateInvoiceRequest(
            student_id=sample_student.id,
            amount=Decimal("1500.00"),
            due_date=due_date,
            description="Tuition Fee",
            late_fee_policy=standard_late_fee_policy,
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.due_date == due_date

    async def test_execute_persists_invoice_to_repository(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute persists invoice to repository."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = CreateInvoiceUseCase()
        request = CreateInvoiceRequest(
            student_id=sample_student.id,
            amount=Decimal("1500.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Tuition Fee",
            late_fee_policy=standard_late_fee_policy,
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        saved = await uow.invoices.get_by_id(result.id)
        assert saved is not None
        assert saved.amount == Decimal("1500.00")

    async def test_execute_commits_transaction(
        self,
        uow: InMemoryUnitOfWork,
        sample_school: School,
        sample_student: Student,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute commits the transaction."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)
        uow.reset_tracking()
        use_case = CreateInvoiceUseCase()
        request = CreateInvoiceRequest(
            student_id=sample_student.id,
            amount=Decimal("1500.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Tuition Fee",
            late_fee_policy=standard_late_fee_policy,
        )

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        assert uow.committed is True

    async def test_execute_raises_when_student_not_found(
        self,
        uow: InMemoryUnitOfWork,
        fixed_student_id: StudentId,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises StudentNotFoundError when student doesn't exist."""
        # Arrange
        use_case = CreateInvoiceUseCase()
        request = CreateInvoiceRequest(
            student_id=fixed_student_id,
            amount=Decimal("1500.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Tuition Fee",
            late_fee_policy=standard_late_fee_policy,
        )

        # Act & Assert
        with pytest.raises(StudentNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_student_id.value) in str(exc_info.value)


# ============================================================================
# CancelInvoiceUseCase
# ============================================================================


class TestCancelInvoiceUseCase:
    """Tests for CancelInvoiceUseCase."""

    async def test_execute_cancels_pending_invoice(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute cancels a pending invoice."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = CancelInvoiceUseCase()
        request = CancelInvoiceRequest(
            invoice_id=sample_invoice.id,
            cancellation_reason="Test cancellation",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.status == InvoiceStatus.CANCELLED

    async def test_execute_persists_cancelled_invoice(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute persists the cancelled invoice."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = CancelInvoiceUseCase()
        request = CancelInvoiceRequest(
            invoice_id=sample_invoice.id,
            cancellation_reason="Test cancellation",
        )

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        saved = await uow.invoices.get_by_id(sample_invoice.id)
        assert saved is not None
        assert saved.status == InvoiceStatus.CANCELLED

    async def test_execute_commits_transaction(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute commits the transaction."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = CancelInvoiceUseCase()
        request = CancelInvoiceRequest(
            invoice_id=sample_invoice.id,
            cancellation_reason="Test cancellation",
        )

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        assert uow.committed is True

    async def test_execute_raises_when_invoice_not_found(
        self,
        uow: InMemoryUnitOfWork,
        fixed_invoice_id: InvoiceId,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises InvoiceNotFoundError when invoice doesn't exist."""
        # Arrange
        use_case = CancelInvoiceUseCase()
        request = CancelInvoiceRequest(
            invoice_id=fixed_invoice_id,
            cancellation_reason="Test cancellation",
        )

        # Act & Assert
        with pytest.raises(InvoiceNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_invoice_id.value) in str(exc_info.value)

    async def test_execute_raises_when_invoice_already_paid(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises InvalidStateTransitionError when invoice is paid."""
        # Arrange
        paid_invoice = sample_invoice.update_status(InvoiceStatus.PAID, fixed_time)
        await uow.invoices.save(paid_invoice)
        uow.reset_tracking()
        use_case = CancelInvoiceUseCase()
        request = CancelInvoiceRequest(
            invoice_id=paid_invoice.id,
            cancellation_reason="Test cancellation",
        )

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            await use_case.execute(uow, request, fixed_time)

    async def test_execute_cancels_partially_paid_invoice(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute can cancel a partially paid invoice."""
        # Arrange
        partial_invoice = sample_invoice.update_status(
            InvoiceStatus.PARTIALLY_PAID, fixed_time
        )
        await uow.invoices.save(partial_invoice)
        uow.reset_tracking()
        use_case = CancelInvoiceUseCase()
        request = CancelInvoiceRequest(
            invoice_id=partial_invoice.id,
            cancellation_reason="Test cancellation",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.status == InvoiceStatus.CANCELLED


# ============================================================================
# ListInvoicesUseCase
# ============================================================================


class TestListInvoicesUseCase:
    """Tests for ListInvoicesUseCase."""

    async def test_execute_returns_empty_page_when_no_invoices(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns empty page when no invoices exist."""
        # Arrange
        use_case = ListInvoicesUseCase()
        filters = InvoiceFilters()
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 0
        assert len(result.items) == 0

    async def test_execute_returns_all_invoices(
        self,
        uow: InMemoryUnitOfWork,
        fixed_student_id: StudentId,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns all invoices when no filters applied."""
        # Arrange
        invoice1 = Invoice.create(
            student_id=fixed_student_id,
            amount=Decimal("1000.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Invoice 1",
            late_fee_policy=standard_late_fee_policy,
            now=fixed_time,
        )
        invoice2 = Invoice.create(
            student_id=fixed_student_id,
            amount=Decimal("2000.00"),
            due_date=datetime(2024, 3, 15, tzinfo=UTC),
            description="Invoice 2",
            late_fee_policy=standard_late_fee_policy,
            now=fixed_time,
        )
        await uow.invoices.save(invoice1)
        await uow.invoices.save(invoice2)

        use_case = ListInvoicesUseCase()
        filters = InvoiceFilters()
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 2
        assert len(result.items) == 2

    async def test_execute_applies_student_filter(
        self,
        uow: InMemoryUnitOfWork,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute filters invoices by student_id."""
        # Arrange
        student1_id = StudentId(value=UUID("11111111-1111-1111-1111-111111111111"))
        student2_id = StudentId(value=UUID("22222222-2222-2222-2222-222222222222"))

        invoice1 = Invoice.create(
            student_id=student1_id,
            amount=Decimal("1000.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Invoice 1",
            late_fee_policy=standard_late_fee_policy,
            now=fixed_time,
        )
        invoice2 = Invoice.create(
            student_id=student2_id,
            amount=Decimal("2000.00"),
            due_date=datetime(2024, 3, 15, tzinfo=UTC),
            description="Invoice 2",
            late_fee_policy=standard_late_fee_policy,
            now=fixed_time,
        )
        await uow.invoices.save(invoice1)
        await uow.invoices.save(invoice2)

        use_case = ListInvoicesUseCase()
        filters = InvoiceFilters(student_id=student1_id.value)
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 1
        assert result.items[0].student_id == student1_id

    async def test_execute_applies_status_filter(
        self,
        uow: InMemoryUnitOfWork,
        fixed_student_id: StudentId,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute filters invoices by status."""
        # Arrange
        pending_invoice = Invoice.create(
            student_id=fixed_student_id,
            amount=Decimal("1000.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Pending Invoice",
            late_fee_policy=standard_late_fee_policy,
            now=fixed_time,
        )
        paid_invoice = Invoice.create(
            student_id=fixed_student_id,
            amount=Decimal("2000.00"),
            due_date=datetime(2024, 3, 15, tzinfo=UTC),
            description="Paid Invoice",
            late_fee_policy=standard_late_fee_policy,
            now=fixed_time,
        ).update_status(InvoiceStatus.PAID, fixed_time)

        await uow.invoices.save(pending_invoice)
        await uow.invoices.save(paid_invoice)

        use_case = ListInvoicesUseCase()
        filters = InvoiceFilters(status=InvoiceStatus.PENDING.value)
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 1
        assert result.items[0].status == InvoiceStatus.PENDING

    async def test_execute_applies_pagination(
        self,
        uow: InMemoryUnitOfWork,
        fixed_student_id: StudentId,
        standard_late_fee_policy: LateFeePolicy,
        fixed_time: datetime,
    ) -> None:
        """Test execute applies pagination correctly."""
        # Arrange
        for i in range(5):
            invoice = Invoice.create(
                student_id=fixed_student_id,
                amount=Decimal(f"{(i + 1) * 100}.00"),
                due_date=datetime(2024, 2, 15, tzinfo=UTC),
                description=f"Invoice {i}",
                late_fee_policy=standard_late_fee_policy,
                now=fixed_time,
            )
            await uow.invoices.save(invoice)

        use_case = ListInvoicesUseCase()
        filters = InvoiceFilters()
        pagination = PaginationParams(offset=0, limit=2)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 5
        assert len(result.items) == 2
