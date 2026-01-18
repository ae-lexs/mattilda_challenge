from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType

from mattilda_challenge.application.ports import (
    InvoiceRepository,
    PaymentRepository,
    SchoolRepository,
    StudentRepository,
)


class UnitOfWork(ABC):
    """
    Port for transactional operations across repositories.

    Contract:
    - All repository properties share the same transaction context
    - commit() persists all changes atomically
    - rollback() discards all changes
    - Auto-rollback on exception when used as context manager

    Usage:
        async with uow:
            await uow.invoices.save(invoice)
            await uow.payments.save(payment)
            await uow.commit()  # Atomic
    """

    @property
    @abstractmethod
    def schools(self) -> SchoolRepository:
        """School repository within this transaction."""
        ...

    @property
    @abstractmethod
    def students(self) -> StudentRepository:
        """Student repository within this transaction."""
        ...

    @property
    @abstractmethod
    def invoices(self) -> InvoiceRepository:
        """Invoice repository within this transaction."""
        ...

    @property
    @abstractmethod
    def payments(self) -> PaymentRepository:
        """Payment repository within this transaction."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit all changes atomically."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback all changes."""
        ...

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork:
        """Enter transaction context."""
        ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit with auto-rollback on exception."""
        ...
