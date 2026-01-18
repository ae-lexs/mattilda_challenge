"""In-memory Unit of Work adapter for testing."""

from __future__ import annotations

from types import TracebackType

from mattilda_challenge.application.ports import (
    InvoiceRepository,
    PaymentRepository,
    SchoolRepository,
    StudentRepository,
    UnitOfWork,
)
from mattilda_challenge.domain.value_objects import InvoiceId, StudentId
from mattilda_challenge.infrastructure.adapters import (
    InMemoryInvoiceRepository,
    InMemoryPaymentRepository,
    InMemorySchoolRepository,
    InMemoryStudentRepository,
)


class InMemoryUnitOfWork(UnitOfWork):
    """
    In-memory adapter for the UnitOfWork port.

    Stores all data in memory using in-memory repository implementations.
    Provides tracking for commit/rollback calls to verify use case behavior.

    Designed for unit testing use cases without database dependencies.

    Usage in tests:
        uow = InMemoryUnitOfWork()

        # Setup test data
        await uow.students.save(test_student)

        # Execute use case
        use_case = CreateInvoiceUseCase()
        result = await use_case.execute(uow, request, now)

        # Verify transaction behavior
        assert uow.committed is True
        assert result.student_id == test_student.id
    """

    def __init__(self) -> None:
        """Initialize with fresh in-memory repositories."""
        self._schools = InMemorySchoolRepository()
        self._students = InMemoryStudentRepository()
        self._invoices = InMemoryInvoiceRepository()
        self._payments = InMemoryPaymentRepository()

        # Tracking for test assertions
        self._committed = False
        self._rolled_back = False

    @property
    def schools(self) -> SchoolRepository:
        """School repository within this transaction."""
        return self._schools

    @property
    def students(self) -> StudentRepository:
        """Student repository within this transaction."""
        return self._students

    @property
    def invoices(self) -> InvoiceRepository:
        """Invoice repository within this transaction."""
        return self._invoices

    @property
    def payments(self) -> PaymentRepository:
        """Payment repository within this transaction."""
        return self._payments

    async def commit(self) -> None:
        """Mark as committed (no-op in memory, tracks for testing)."""
        self._committed = True

    async def rollback(self) -> None:
        """Mark as rolled back (no-op in memory, tracks for testing)."""
        self._rolled_back = True

    async def __aenter__(self) -> InMemoryUnitOfWork:
        """Enter transaction context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit with auto-rollback on exception."""
        if exc_type is not None:
            await self.rollback()

    # =========================================================================
    # Test helper properties and methods (not part of port interface)
    # =========================================================================

    @property
    def committed(self) -> bool:
        """Check if commit() was called (test utility)."""
        return self._committed

    @property
    def rolled_back(self) -> bool:
        """Check if rollback() was called (test utility)."""
        return self._rolled_back

    def reset_tracking(self) -> None:
        """Reset commit/rollback tracking (test utility)."""
        self._committed = False
        self._rolled_back = False

    def clear_all(self) -> None:
        """Clear all repositories and reset tracking (test utility)."""
        self._schools.clear()
        self._students.clear()
        self._invoices.clear()
        self._payments.clear()
        self.reset_tracking()

    def set_invoice_student_mapping(
        self,
        invoice_id: InvoiceId,
        student_id: StudentId,
    ) -> None:
        """
        Set invoice->student mapping for payment repository.

        Required for get_total_by_student to work correctly in the
        in-memory implementation, since it cannot perform joins.

        Args:
            invoice_id: Invoice identifier
            student_id: Student who owns the invoice
        """
        self._payments.set_invoice_student_mapping(invoice_id, student_id)
