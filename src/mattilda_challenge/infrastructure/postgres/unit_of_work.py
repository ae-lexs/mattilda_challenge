# infrastructure/postgres/unit_of_work.py
from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.ports import (
    InvoiceRepository,
    PaymentRepository,
    SchoolRepository,
    StudentRepository,
)
from mattilda_challenge.infrastructure.adapters import (
    PostgresInvoiceRepository,
    PostgresPaymentRepository,
    PostgresSchoolRepository,
    PostgresStudentRepository,
)


class UnitOfWork:
    """
    Unit of Work pattern for transactional operations.

    Ensures all repositories in a use case share the same session
    and transaction. Provides atomic commit/rollback.

    Usage:
        async with UnitOfWork(session) as uow:
            # All operations share same transaction
            payment = await uow.payments.save(payment)
            invoice = await uow.invoices.get_by_id(invoice_id, for_update=True)
            updated = invoice.record_payment(payment.amount, now)
            await uow.invoices.save(updated)

            # Atomic commit
            await uow.commit()
    """

    def __init__(self, session: AsyncSession):
        self._session = session

        # All repositories share the same session (same transaction)
        self.schools: SchoolRepository = PostgresSchoolRepository(session)
        self.students: StudentRepository = PostgresStudentRepository(session)
        self.invoices: InvoiceRepository = PostgresInvoiceRepository(session)
        self.payments: PaymentRepository = PostgresPaymentRepository(session)

    async def __aenter__(self) -> UnitOfWork:
        """Enter transaction context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit transaction context with rollback on error.

        Note: Session lifecycle is managed by FastAPI's get_session() dependency.
        UoW only owns transaction scope (commit/rollback), not session lifetime.
        """
        if exc_type is not None:
            await self.rollback()
        # Session closing is handled by get_session() - do NOT close here

    async def commit(self) -> None:
        """Commit all changes atomically."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback all changes."""
        await self._session.rollback()
