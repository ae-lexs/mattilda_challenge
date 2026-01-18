"""Unit tests for Account Statement use cases.

Tests for GetStudentAccountStatementUseCase and GetSchoolAccountStatementUseCase
following the Arrange-Act-Assert pattern.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from mattilda_challenge.application.dtos import (
    SchoolAccountStatement,
    StudentAccountStatement,
)
from mattilda_challenge.application.ports import (
    SchoolAccountStatementCache,
    StudentAccountStatementCache,
)
from mattilda_challenge.application.use_cases import (
    GetSchoolAccountStatementUseCase,
    GetStudentAccountStatementUseCase,
)
from mattilda_challenge.application.use_cases.requests import (
    GetSchoolAccountStatementRequest,
    GetStudentAccountStatementRequest,
)
from mattilda_challenge.domain.entities import Invoice, Payment, School, Student
from mattilda_challenge.domain.exceptions import (
    SchoolNotFoundError,
    StudentNotFoundError,
)
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    PaymentId,
    SchoolId,
    StudentId,
    StudentStatus,
)
from mattilda_challenge.infrastructure.adapters import InMemoryUnitOfWork

# ============================================================================
# In-Memory Cache Implementations for Testing
# ============================================================================


class InMemoryStudentAccountStatementCache(StudentAccountStatementCache):
    """In-memory cache for testing student account statements."""

    def __init__(self) -> None:
        self._cache: dict[StudentId, StudentAccountStatement] = {}

    async def get(self, student_id: StudentId) -> StudentAccountStatement | None:
        return self._cache.get(student_id)

    async def set(self, statement: StudentAccountStatement) -> None:
        self._cache[statement.student_id] = statement

    def clear(self) -> None:
        self._cache.clear()


class InMemorySchoolAccountStatementCache(SchoolAccountStatementCache):
    """In-memory cache for testing school account statements."""

    def __init__(self) -> None:
        self._cache: dict[SchoolId, SchoolAccountStatement] = {}

    async def get(self, school_id: SchoolId) -> SchoolAccountStatement | None:
        return self._cache.get(school_id)

    async def set(self, statement: SchoolAccountStatement) -> None:
        self._cache[statement.school_id] = statement

    def clear(self) -> None:
        self._cache.clear()


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
def uow() -> InMemoryUnitOfWork:
    """Provide fresh InMemoryUnitOfWork for each test."""
    return InMemoryUnitOfWork()


@pytest.fixture
def student_cache() -> InMemoryStudentAccountStatementCache:
    """Provide fresh student statement cache for each test."""
    return InMemoryStudentAccountStatementCache()


@pytest.fixture
def school_cache() -> InMemorySchoolAccountStatementCache:
    """Provide fresh school statement cache for each test."""
    return InMemorySchoolAccountStatementCache()


# ============================================================================
# GetStudentAccountStatementUseCase
# ============================================================================


class TestGetStudentAccountStatementUseCase:
    """Tests for GetStudentAccountStatementUseCase."""

    async def test_execute_returns_cached_statement_on_cache_hit(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        fixed_student_id: StudentId,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns cached statement when cache hit occurs."""
        # Arrange
        cached_statement = StudentAccountStatement(
            student_id=fixed_student_id,
            student_name="John Doe",
            school_name="Test School",
            total_invoiced=Decimal("1000.00"),
            total_paid=Decimal("500.00"),
            total_pending=Decimal("500.00"),
            invoices_pending=1,
            invoices_partially_paid=0,
            invoices_paid=0,
            invoices_cancelled=0,
            invoices_overdue=0,
            total_late_fees=Decimal("0"),
            statement_date=fixed_time,
        )
        await student_cache.set(cached_statement)

        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=fixed_student_id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result == cached_statement

    async def test_execute_computes_statement_on_cache_miss(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute computes statement from database on cache miss."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=sample_student.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.student_id == sample_student.id
        assert result.student_name == "John Doe"
        assert result.school_name == "Test School"

    async def test_execute_caches_computed_statement(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute caches the computed statement."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=sample_student.id)

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        cached = await student_cache.get(sample_student.id)
        assert cached is not None
        assert cached.student_id == sample_student.id

    async def test_execute_raises_when_student_not_found(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        fixed_student_id: StudentId,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises StudentNotFoundError when student doesn't exist."""
        # Arrange
        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=fixed_student_id)

        # Act & Assert
        with pytest.raises(StudentNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_student_id.value) in str(exc_info.value)

    async def test_execute_calculates_correct_total_invoiced(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute calculates total invoiced correctly."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        invoice1 = Invoice(
            id=InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000001",
            amount=Decimal("500.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Invoice 1",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        invoice2 = Invoice(
            id=InvoiceId(value=UUID("44444444-4444-4444-4444-444444444444")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000002",
            amount=Decimal("750.00"),
            due_date=datetime(2024, 3, 15, tzinfo=UTC),
            description="Invoice 2",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.invoices.save(invoice1)
        await uow.invoices.save(invoice2)

        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=sample_student.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.total_invoiced == Decimal("1250.00")

    async def test_execute_calculates_correct_total_paid(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute calculates total paid correctly."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        invoice = Invoice(
            id=InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000001",
            amount=Decimal("1000.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Invoice 1",
            status=InvoiceStatus.PARTIALLY_PAID,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.invoices.save(invoice)

        # Set up invoice-student mapping for payment total calculation
        uow.set_invoice_student_mapping(invoice.id, sample_student.id)

        payment1 = Payment(
            id=PaymentId(value=UUID("55555555-5555-5555-5555-555555555555")),
            invoice_id=invoice.id,
            amount=Decimal("300.00"),
            payment_date=fixed_time,
            payment_method="cash",
            reference_number=None,
            created_at=fixed_time,
        )
        payment2 = Payment(
            id=PaymentId(value=UUID("66666666-6666-6666-6666-666666666666")),
            invoice_id=invoice.id,
            amount=Decimal("200.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
            reference_number=None,
            created_at=fixed_time,
        )
        await uow.payments.save(payment1)
        await uow.payments.save(payment2)

        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=sample_student.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.total_paid == Decimal("500.00")

    async def test_execute_calculates_correct_total_pending(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute calculates total pending (invoiced - paid)."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        invoice = Invoice(
            id=InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000001",
            amount=Decimal("1000.00"),
            due_date=datetime(2024, 2, 15, tzinfo=UTC),
            description="Invoice 1",
            status=InvoiceStatus.PARTIALLY_PAID,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.invoices.save(invoice)

        uow.set_invoice_student_mapping(invoice.id, sample_student.id)

        payment = Payment(
            id=PaymentId(value=UUID("55555555-5555-5555-5555-555555555555")),
            invoice_id=invoice.id,
            amount=Decimal("400.00"),
            payment_date=fixed_time,
            payment_method="cash",
            reference_number=None,
            created_at=fixed_time,
        )
        await uow.payments.save(payment)

        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=sample_student.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.total_pending == Decimal("600.00")

    async def test_execute_counts_invoices_by_status(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute counts invoices by status correctly."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        pending_invoice = Invoice(
            id=InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000001",
            amount=Decimal("100.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Pending",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        partial_invoice = Invoice(
            id=InvoiceId(value=UUID("44444444-4444-4444-4444-444444444444")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000002",
            amount=Decimal("200.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Partial",
            status=InvoiceStatus.PARTIALLY_PAID,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        paid_invoice = Invoice(
            id=InvoiceId(value=UUID("55555555-5555-5555-5555-555555555555")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000003",
            amount=Decimal("300.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Paid",
            status=InvoiceStatus.PAID,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        cancelled_invoice = Invoice(
            id=InvoiceId(value=UUID("66666666-6666-6666-6666-666666666666")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000004",
            amount=Decimal("400.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Cancelled",
            status=InvoiceStatus.CANCELLED,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.invoices.save(pending_invoice)
        await uow.invoices.save(partial_invoice)
        await uow.invoices.save(paid_invoice)
        await uow.invoices.save(cancelled_invoice)

        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=sample_student.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.invoices_pending == 1
        assert result.invoices_partially_paid == 1
        assert result.invoices_paid == 1
        assert result.invoices_cancelled == 1

    async def test_execute_counts_overdue_invoices(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        sample_school: School,
        sample_student: Student,
    ) -> None:
        """Test execute counts overdue invoices correctly."""
        # Arrange
        creation_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        check_time = datetime(2024, 3, 15, 12, 0, 0, tzinfo=UTC)

        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        overdue_invoice = Invoice(
            id=InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000001",
            amount=Decimal("100.00"),
            due_date=datetime(2024, 2, 1, tzinfo=UTC),  # Due date before check_time
            description="Overdue",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=creation_time,
            updated_at=creation_time,
        )
        not_overdue_invoice = Invoice(
            id=InvoiceId(value=UUID("44444444-4444-4444-4444-444444444444")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000002",
            amount=Decimal("200.00"),
            due_date=datetime(2024, 6, 1, tzinfo=UTC),  # Due date after check_time
            description="Not Overdue",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=creation_time,
            updated_at=creation_time,
        )
        await uow.invoices.save(overdue_invoice)
        await uow.invoices.save(not_overdue_invoice)

        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=sample_student.id)

        # Act
        result = await use_case.execute(uow, request, check_time)

        # Assert
        assert result.invoices_overdue == 1

    async def test_execute_returns_zero_totals_for_student_without_invoices(
        self,
        uow: InMemoryUnitOfWork,
        student_cache: InMemoryStudentAccountStatementCache,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns zero totals for student with no invoices."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        use_case = GetStudentAccountStatementUseCase(cache=student_cache)
        request = GetStudentAccountStatementRequest(student_id=sample_student.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.total_invoiced == Decimal("0")
        assert result.total_paid == Decimal("0")
        assert result.total_pending == Decimal("0")
        assert result.invoices_pending == 0
        assert result.invoices_overdue == 0


# ============================================================================
# GetSchoolAccountStatementUseCase
# ============================================================================


class TestGetSchoolAccountStatementUseCase:
    """Tests for GetSchoolAccountStatementUseCase."""

    async def test_execute_returns_cached_statement_on_cache_hit(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns cached statement when cache hit occurs."""
        # Arrange
        cached_statement = SchoolAccountStatement(
            school_id=fixed_school_id,
            school_name="Test School",
            total_students=5,
            active_students=4,
            total_invoiced=Decimal("5000.00"),
            total_paid=Decimal("2500.00"),
            total_pending=Decimal("2500.00"),
            invoices_pending=3,
            invoices_partially_paid=1,
            invoices_paid=2,
            invoices_overdue=1,
            invoices_cancelled=0,
            total_late_fees=Decimal("50.00"),
            statement_date=fixed_time,
        )
        await school_cache.set(cached_statement)

        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=fixed_school_id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result == cached_statement

    async def test_execute_computes_statement_on_cache_miss(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute computes statement from database on cache miss."""
        # Arrange
        await uow.schools.save(sample_school)

        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=sample_school.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.school_id == sample_school.id
        assert result.school_name == "Test School"

    async def test_execute_caches_computed_statement(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute caches the computed statement."""
        # Arrange
        await uow.schools.save(sample_school)

        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=sample_school.id)

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        cached = await school_cache.get(sample_school.id)
        assert cached is not None
        assert cached.school_id == sample_school.id

    async def test_execute_raises_when_school_not_found(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises SchoolNotFoundError when school doesn't exist."""
        # Arrange
        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=fixed_school_id)

        # Act & Assert
        with pytest.raises(SchoolNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_school_id.value) in str(exc_info.value)

    async def test_execute_counts_total_students(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute counts total students correctly."""
        # Arrange
        await uow.schools.save(sample_school)

        student1 = Student(
            id=StudentId(value=UUID("22222222-2222-2222-2222-222222222222")),
            school_id=sample_school.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            enrollment_date=fixed_time,
            status=StudentStatus.ACTIVE,
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        student2 = Student(
            id=StudentId(value=UUID("33333333-3333-3333-3333-333333333333")),
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            enrollment_date=fixed_time,
            status=StudentStatus.INACTIVE,
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.students.save(student1)
        await uow.students.save(student2)

        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=sample_school.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.total_students == 2

    async def test_execute_counts_active_students(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute counts active students correctly."""
        # Arrange
        await uow.schools.save(sample_school)

        active_student = Student(
            id=StudentId(value=UUID("22222222-2222-2222-2222-222222222222")),
            school_id=sample_school.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            enrollment_date=fixed_time,
            status=StudentStatus.ACTIVE,
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        inactive_student = Student(
            id=StudentId(value=UUID("33333333-3333-3333-3333-333333333333")),
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            enrollment_date=fixed_time,
            status=StudentStatus.INACTIVE,
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        graduated_student = Student(
            id=StudentId(value=UUID("44444444-4444-4444-4444-444444444444")),
            school_id=sample_school.id,
            first_name="Bob",
            last_name="Johnson",
            email="bob@test.com",
            enrollment_date=fixed_time,
            status=StudentStatus.GRADUATED,
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.students.save(active_student)
        await uow.students.save(inactive_student)
        await uow.students.save(graduated_student)

        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=sample_school.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.total_students == 3
        assert result.active_students == 1

    async def test_execute_aggregates_totals_across_students(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute aggregates financial totals across all students."""
        # Arrange
        await uow.schools.save(sample_school)

        student1 = Student(
            id=StudentId(value=UUID("22222222-2222-2222-2222-222222222222")),
            school_id=sample_school.id,
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            enrollment_date=fixed_time,
            status=StudentStatus.ACTIVE,
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        student2 = Student(
            id=StudentId(value=UUID("33333333-3333-3333-3333-333333333333")),
            school_id=sample_school.id,
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            enrollment_date=fixed_time,
            status=StudentStatus.ACTIVE,
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.students.save(student1)
        await uow.students.save(student2)

        invoice1 = Invoice(
            id=InvoiceId(value=UUID("44444444-4444-4444-4444-444444444444")),
            student_id=student1.id,
            invoice_number="INV-2024-000001",
            amount=Decimal("500.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Invoice 1",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        invoice2 = Invoice(
            id=InvoiceId(value=UUID("55555555-5555-5555-5555-555555555555")),
            student_id=student2.id,
            invoice_number="INV-2024-000002",
            amount=Decimal("750.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Invoice 2",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.invoices.save(invoice1)
        await uow.invoices.save(invoice2)

        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=sample_school.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.total_invoiced == Decimal("1250.00")

    async def test_execute_counts_invoices_by_status(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        sample_school: School,
        sample_student: Student,
        fixed_time: datetime,
    ) -> None:
        """Test execute counts invoices by status correctly."""
        # Arrange
        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        pending_invoice = Invoice(
            id=InvoiceId(value=UUID("44444444-4444-4444-4444-444444444444")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000001",
            amount=Decimal("100.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Pending",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        partially_paid_invoice = Invoice(
            id=InvoiceId(value=UUID("55555555-5555-5555-5555-555555555555")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000002",
            amount=Decimal("200.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Partially Paid",
            status=InvoiceStatus.PARTIALLY_PAID,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        paid_invoice = Invoice(
            id=InvoiceId(value=UUID("66666666-6666-6666-6666-666666666666")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000003",
            amount=Decimal("300.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Paid",
            status=InvoiceStatus.PAID,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        cancelled_invoice = Invoice(
            id=InvoiceId(value=UUID("77777777-7777-7777-7777-777777777777")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000004",
            amount=Decimal("400.00"),
            due_date=datetime(2024, 6, 15, tzinfo=UTC),
            description="Cancelled",
            status=InvoiceStatus.CANCELLED,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        await uow.invoices.save(pending_invoice)
        await uow.invoices.save(partially_paid_invoice)
        await uow.invoices.save(paid_invoice)
        await uow.invoices.save(cancelled_invoice)

        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=sample_school.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.invoices_pending == 1
        assert result.invoices_partially_paid == 1
        assert result.invoices_paid == 1
        assert result.invoices_cancelled == 1

    async def test_execute_counts_overdue_invoices_and_calculates_late_fees(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        sample_school: School,
        sample_student: Student,
    ) -> None:
        """Test execute counts overdue invoices and calculates late fees."""
        # Arrange
        creation_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        check_time = datetime(2024, 3, 15, 12, 0, 0, tzinfo=UTC)

        await uow.schools.save(sample_school)
        await uow.students.save(sample_student)

        # Overdue PENDING invoice (due Feb 1, checking March 15 = ~1.5 months overdue)
        overdue_pending = Invoice(
            id=InvoiceId(value=UUID("44444444-4444-4444-4444-444444444444")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000001",
            amount=Decimal("1000.00"),
            due_date=datetime(2024, 2, 1, tzinfo=UTC),
            description="Overdue Pending",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=creation_time,
            updated_at=creation_time,
        )
        # Overdue PARTIALLY_PAID invoice
        overdue_partial = Invoice(
            id=InvoiceId(value=UUID("55555555-5555-5555-5555-555555555555")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000002",
            amount=Decimal("500.00"),
            due_date=datetime(2024, 2, 1, tzinfo=UTC),
            description="Overdue Partial",
            status=InvoiceStatus.PARTIALLY_PAID,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=creation_time,
            updated_at=creation_time,
        )
        # Not overdue (future due date)
        not_overdue = Invoice(
            id=InvoiceId(value=UUID("66666666-6666-6666-6666-666666666666")),
            student_id=sample_student.id,
            invoice_number="INV-2024-000003",
            amount=Decimal("200.00"),
            due_date=datetime(2024, 6, 1, tzinfo=UTC),
            description="Not Overdue",
            status=InvoiceStatus.PENDING,
            late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
            created_at=creation_time,
            updated_at=creation_time,
        )
        await uow.invoices.save(overdue_pending)
        await uow.invoices.save(overdue_partial)
        await uow.invoices.save(not_overdue)

        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=sample_school.id)

        # Act
        result = await use_case.execute(uow, request, check_time)

        # Assert
        assert result.invoices_overdue == 2
        assert result.total_late_fees > Decimal("0")

    async def test_execute_returns_zero_totals_for_school_without_students(
        self,
        uow: InMemoryUnitOfWork,
        school_cache: InMemorySchoolAccountStatementCache,
        sample_school: School,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns zero totals for school with no students."""
        # Arrange
        await uow.schools.save(sample_school)

        use_case = GetSchoolAccountStatementUseCase(cache=school_cache)
        request = GetSchoolAccountStatementRequest(school_id=sample_school.id)

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.total_students == 0
        assert result.active_students == 0
        assert result.total_invoiced == Decimal("0")
        assert result.total_paid == Decimal("0")
        assert result.total_pending == Decimal("0")
