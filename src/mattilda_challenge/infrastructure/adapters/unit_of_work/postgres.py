"""PostgreSQL Unit of Work adapter."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.ports import (
    InvoiceRepository,
    PaymentRepository,
    SchoolRepository,
    StudentRepository,
    UnitOfWork,
)
from mattilda_challenge.infrastructure.adapters import (
    PostgresInvoiceRepository,
    PostgresPaymentRepository,
    PostgresSchoolRepository,
    PostgresStudentRepository,
)


class PostgresUnitOfWork(UnitOfWork):
    """
    PostgreSQL adapter for the UnitOfWork port.

    Provides transactional operations across all repositories using
    a shared SQLAlchemy AsyncSession. All repositories within a single
    UoW instance share the same database transaction.

    Usage:
        async with PostgresUnitOfWork(session) as uow:
            # All operations share same transaction
            payment = await uow.payments.save(payment)
            invoice = await uow.invoices.get_by_id(invoice_id, for_update=True)
            updated = invoice.update_status(new_status, now)
            await uow.invoices.save(updated)

            # Atomic commit
            await uow.commit()

    Note:
        Session lifecycle is managed externally (e.g., by FastAPI dependency).
        UoW only owns transaction scope (commit/rollback), not session lifetime.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize with a shared database session.

        Args:
            session: SQLAlchemy AsyncSession (externally managed)
        """
        self._session = session

        # Initialize all repositories with shared session
        self._schools = PostgresSchoolRepository(session)
        self._students = PostgresStudentRepository(session)
        self._invoices = PostgresInvoiceRepository(session)
        self._payments = PostgresPaymentRepository(session)

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
        """Commit all changes atomically."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback all changes."""
        await self._session.rollback()

    async def __aenter__(self) -> PostgresUnitOfWork:
        """Enter transaction context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exit transaction context with auto-rollback on exception.

        Note: Session closing is handled externally - do NOT close here.
        """
        if exc_type is not None:
            await self.rollback()
