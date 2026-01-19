"""Unit tests for InMemoryUnitOfWork.

These tests verify the in-memory Unit of Work adapter implementation that
provides transactional semantics for unit testing use cases. The InMemoryUnitOfWork:
- Provides in-memory repository instances for each aggregate
- Tracks commit/rollback calls for test assertions
- Auto-rollbacks on exception in context manager exit
- Provides test helper methods for setup and cleanup
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from mattilda_challenge.domain.entities import Invoice, School, Student
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    LateFeePolicy,
    SchoolId,
    StudentId,
)
from mattilda_challenge.infrastructure.adapters import (
    InMemoryInvoiceRepository,
    InMemoryPaymentRepository,
    InMemorySchoolRepository,
    InMemoryStudentRepository,
    InMemoryUnitOfWork,
)

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
) -> Invoice:
    """Provide sample invoice entity for testing."""
    return Invoice.create(
        student_id=fixed_student_id,
        amount=Decimal("1000.00"),
        due_date=datetime(2024, 2, 15, tzinfo=UTC),
        description="Test Invoice",
        late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
        now=fixed_time,
    )


# ============================================================================
# Initialization
# ============================================================================


class TestInMemoryUnitOfWorkInit:
    """Tests for InMemoryUnitOfWork initialization."""

    def test_init_creates_schools_repository(self) -> None:
        """Test InMemoryUnitOfWork creates schools repository."""
        uow = InMemoryUnitOfWork()

        assert isinstance(uow.schools, InMemorySchoolRepository)

    def test_init_creates_students_repository(self) -> None:
        """Test InMemoryUnitOfWork creates students repository."""
        uow = InMemoryUnitOfWork()

        assert isinstance(uow.students, InMemoryStudentRepository)

    def test_init_creates_invoices_repository(self) -> None:
        """Test InMemoryUnitOfWork creates invoices repository."""
        uow = InMemoryUnitOfWork()

        assert isinstance(uow.invoices, InMemoryInvoiceRepository)

    def test_init_creates_payments_repository(self) -> None:
        """Test InMemoryUnitOfWork creates payments repository."""
        uow = InMemoryUnitOfWork()

        assert isinstance(uow.payments, InMemoryPaymentRepository)

    def test_init_committed_is_false(self) -> None:
        """Test InMemoryUnitOfWork initializes with committed as False."""
        uow = InMemoryUnitOfWork()

        assert uow.committed is False

    def test_init_rolled_back_is_false(self) -> None:
        """Test InMemoryUnitOfWork initializes with rolled_back as False."""
        uow = InMemoryUnitOfWork()

        assert uow.rolled_back is False


# ============================================================================
# Async Context Manager
# ============================================================================


class TestInMemoryUnitOfWorkContextManager:
    """Tests for async context manager behavior."""

    async def test_aenter_returns_unit_of_work_instance(self) -> None:
        """Test __aenter__ returns the InMemoryUnitOfWork instance."""
        uow = InMemoryUnitOfWork()

        result = await uow.__aenter__()

        assert result is uow

    async def test_aexit_does_not_rollback_when_no_exception(self) -> None:
        """Test __aexit__ does not set rolled_back when context exits normally."""
        uow = InMemoryUnitOfWork()

        await uow.__aexit__(None, None, None)

        assert uow.rolled_back is False

    async def test_aexit_rolls_back_when_exception_occurs(self) -> None:
        """Test __aexit__ sets rolled_back when exception occurs in context."""
        uow = InMemoryUnitOfWork()

        await uow.__aexit__(ValueError, ValueError("test error"), None)

        assert uow.rolled_back is True

    async def test_context_manager_provides_uow_in_with_block(self) -> None:
        """Test InMemoryUnitOfWork provides itself when used as async context manager."""
        async with InMemoryUnitOfWork() as uow:
            assert isinstance(uow, InMemoryUnitOfWork)

    async def test_context_manager_does_not_rollback_on_normal_exit(self) -> None:
        """Test InMemoryUnitOfWork does not rollback on normal exit."""
        uow = InMemoryUnitOfWork()

        async with uow:
            pass

        assert uow.rolled_back is False

    async def test_context_manager_rolls_back_on_raised_exception(self) -> None:
        """Test InMemoryUnitOfWork rolls back when exception is raised within context."""
        uow = InMemoryUnitOfWork()

        with pytest.raises(RuntimeError):
            async with uow:
                raise RuntimeError("simulated failure")

        assert uow.rolled_back is True


# ============================================================================
# Commit
# ============================================================================


class TestInMemoryUnitOfWorkCommit:
    """Tests for commit method."""

    async def test_commit_sets_committed_flag(self) -> None:
        """Test commit() sets the committed flag to True."""
        uow = InMemoryUnitOfWork()

        await uow.commit()

        assert uow.committed is True

    async def test_commit_can_be_called_multiple_times(self) -> None:
        """Test commit() can be called multiple times without error."""
        uow = InMemoryUnitOfWork()

        await uow.commit()
        await uow.commit()

        assert uow.committed is True


# ============================================================================
# Rollback
# ============================================================================


class TestInMemoryUnitOfWorkRollback:
    """Tests for rollback method."""

    async def test_rollback_sets_rolled_back_flag(self) -> None:
        """Test rollback() sets the rolled_back flag to True."""
        uow = InMemoryUnitOfWork()

        await uow.rollback()

        assert uow.rolled_back is True

    async def test_rollback_can_be_called_multiple_times(self) -> None:
        """Test rollback() can be called multiple times without error."""
        uow = InMemoryUnitOfWork()

        await uow.rollback()
        await uow.rollback()

        assert uow.rolled_back is True


# ============================================================================
# Test Helper Methods
# ============================================================================


class TestInMemoryUnitOfWorkResetTracking:
    """Tests for reset_tracking helper method."""

    async def test_reset_tracking_clears_committed_flag(self) -> None:
        """Test reset_tracking() clears the committed flag."""
        uow = InMemoryUnitOfWork()
        await uow.commit()
        assert uow.committed is True

        uow.reset_tracking()

        assert uow.committed is False

    async def test_reset_tracking_clears_rolled_back_flag(self) -> None:
        """Test reset_tracking() clears the rolled_back flag."""
        uow = InMemoryUnitOfWork()
        await uow.rollback()
        assert uow.rolled_back is True

        uow.reset_tracking()

        assert uow.rolled_back is False

    async def test_reset_tracking_clears_both_flags(self) -> None:
        """Test reset_tracking() clears both committed and rolled_back flags."""
        uow = InMemoryUnitOfWork()
        await uow.commit()
        await uow.rollback()

        uow.reset_tracking()

        assert uow.committed is False
        assert uow.rolled_back is False


class TestInMemoryUnitOfWorkClearAll:
    """Tests for clear_all helper method."""

    async def test_clear_all_clears_schools_repository(
        self,
        sample_school: School,
    ) -> None:
        """Test clear_all() clears the schools repository."""
        uow = InMemoryUnitOfWork()
        await uow.schools.save(sample_school)
        saved = await uow.schools.get_by_id(sample_school.id)
        assert saved is not None

        uow.clear_all()

        result = await uow.schools.get_by_id(sample_school.id)
        assert result is None

    async def test_clear_all_clears_students_repository(
        self,
        sample_student: Student,
    ) -> None:
        """Test clear_all() clears the students repository."""
        uow = InMemoryUnitOfWork()
        await uow.students.save(sample_student)
        saved = await uow.students.get_by_id(sample_student.id)
        assert saved is not None

        uow.clear_all()

        result = await uow.students.get_by_id(sample_student.id)
        assert result is None

    async def test_clear_all_clears_invoices_repository(
        self,
        sample_invoice: Invoice,
    ) -> None:
        """Test clear_all() clears the invoices repository."""
        uow = InMemoryUnitOfWork()
        await uow.invoices.save(sample_invoice)
        saved = await uow.invoices.get_by_id(sample_invoice.id)
        assert saved is not None

        uow.clear_all()

        result = await uow.invoices.get_by_id(sample_invoice.id)
        assert result is None

    async def test_clear_all_resets_tracking_flags(self) -> None:
        """Test clear_all() also resets tracking flags."""
        uow = InMemoryUnitOfWork()
        await uow.commit()
        await uow.rollback()

        uow.clear_all()

        assert uow.committed is False
        assert uow.rolled_back is False


class TestInMemoryUnitOfWorkSetInvoiceStudentMapping:
    """Tests for set_invoice_student_mapping helper method."""

    def test_set_invoice_student_mapping_stores_mapping(
        self,
        fixed_invoice_id: InvoiceId,
        fixed_student_id: StudentId,
    ) -> None:
        """Test set_invoice_student_mapping() stores the mapping in payment repository."""
        uow = InMemoryUnitOfWork()

        uow.set_invoice_student_mapping(fixed_invoice_id, fixed_student_id)

        # Verify by checking the internal state of the payment repository
        assert uow._payments._invoice_to_student[fixed_invoice_id] == fixed_student_id


# ============================================================================
# Repository Integration (Data Persistence Within UoW)
# ============================================================================


class TestInMemoryUnitOfWorkRepositoryIntegration:
    """Tests verifying repositories share data within the same UoW instance."""

    async def test_saved_school_is_retrievable(
        self,
        sample_school: School,
    ) -> None:
        """Test school saved through UoW can be retrieved."""
        uow = InMemoryUnitOfWork()

        await uow.schools.save(sample_school)
        result = await uow.schools.get_by_id(sample_school.id)

        assert result is not None
        assert result.id == sample_school.id
        assert result.name == sample_school.name

    async def test_saved_student_is_retrievable(
        self,
        sample_student: Student,
    ) -> None:
        """Test student saved through UoW can be retrieved."""
        uow = InMemoryUnitOfWork()

        await uow.students.save(sample_student)
        result = await uow.students.get_by_id(sample_student.id)

        assert result is not None
        assert result.id == sample_student.id
        assert result.email == sample_student.email

    async def test_saved_invoice_is_retrievable(
        self,
        sample_invoice: Invoice,
    ) -> None:
        """Test invoice saved through UoW can be retrieved."""
        uow = InMemoryUnitOfWork()

        await uow.invoices.save(sample_invoice)
        result = await uow.invoices.get_by_id(sample_invoice.id)

        assert result is not None
        assert result.id == sample_invoice.id
        assert result.amount == sample_invoice.amount

    async def test_different_uow_instances_have_separate_data(
        self,
        sample_school: School,
    ) -> None:
        """Test different UoW instances do not share repository data."""
        uow1 = InMemoryUnitOfWork()
        uow2 = InMemoryUnitOfWork()

        await uow1.schools.save(sample_school)

        # uow2 should not see data from uow1
        result = await uow2.schools.get_by_id(sample_school.id)
        assert result is None
