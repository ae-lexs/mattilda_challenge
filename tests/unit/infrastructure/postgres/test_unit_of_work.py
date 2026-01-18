"""Unit tests for UnitOfWork.

These tests verify the Unit of Work pattern implementation that manages
transactional operations across repositories. Per ADR-004, the UoW:
- Ensures all repositories share the same session (same transaction)
- Provides atomic commit/rollback
- Rolls back on exception in context manager exit
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.infrastructure.adapters import (
    PostgresInvoiceRepository,
    PostgresPaymentRepository,
    PostgresSchoolRepository,
    PostgresStudentRepository,
)
from mattilda_challenge.infrastructure.postgres.unit_of_work import UnitOfWork

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session() -> AsyncMock:
    """Provide mock AsyncSession for testing."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


# ============================================================================
# Initialization
# ============================================================================


class TestUnitOfWorkInit:
    """Tests for UnitOfWork initialization."""

    def test_init_creates_schools_repository_with_session(
        self, mock_session: AsyncMock
    ) -> None:
        """Test UnitOfWork creates schools repository sharing the session."""
        uow = UnitOfWork(mock_session)

        assert isinstance(uow.schools, PostgresSchoolRepository)

    def test_init_creates_students_repository_with_session(
        self, mock_session: AsyncMock
    ) -> None:
        """Test UnitOfWork creates students repository sharing the session."""
        uow = UnitOfWork(mock_session)

        assert isinstance(uow.students, PostgresStudentRepository)

    def test_init_creates_invoices_repository_with_session(
        self, mock_session: AsyncMock
    ) -> None:
        """Test UnitOfWork creates invoices repository sharing the session."""
        uow = UnitOfWork(mock_session)

        assert isinstance(uow.invoices, PostgresInvoiceRepository)

    def test_init_creates_payments_repository_with_session(
        self, mock_session: AsyncMock
    ) -> None:
        """Test UnitOfWork creates payments repository sharing the session."""
        uow = UnitOfWork(mock_session)

        assert isinstance(uow.payments, PostgresPaymentRepository)


# ============================================================================
# Async Context Manager
# ============================================================================


class TestUnitOfWorkContextManager:
    """Tests for async context manager behavior."""

    async def test_aenter_returns_unit_of_work_instance(
        self, mock_session: AsyncMock
    ) -> None:
        """Test __aenter__ returns the UnitOfWork instance for use in context."""
        uow = UnitOfWork(mock_session)

        result = await uow.__aenter__()

        assert result is uow

    async def test_aexit_does_not_rollback_when_no_exception(
        self, mock_session: AsyncMock
    ) -> None:
        """Test __aexit__ does not rollback when context exits without exception."""
        uow = UnitOfWork(mock_session)

        await uow.__aexit__(None, None, None)

        mock_session.rollback.assert_not_called()

    async def test_aexit_rolls_back_when_exception_occurs(
        self, mock_session: AsyncMock
    ) -> None:
        """Test __aexit__ rolls back transaction when exception occurs in context."""
        uow = UnitOfWork(mock_session)

        await uow.__aexit__(ValueError, ValueError("test error"), None)

        mock_session.rollback.assert_awaited_once()

    async def test_context_manager_provides_uow_in_with_block(
        self, mock_session: AsyncMock
    ) -> None:
        """Test UnitOfWork provides itself when used as async context manager."""
        async with UnitOfWork(mock_session) as uow:
            assert isinstance(uow, UnitOfWork)

        mock_session.rollback.assert_not_called()

    async def test_context_manager_rolls_back_on_raised_exception(
        self, mock_session: AsyncMock
    ) -> None:
        """Test UnitOfWork rolls back when exception is raised within context."""
        with pytest.raises(RuntimeError):
            async with UnitOfWork(mock_session):
                raise RuntimeError("simulated failure")

        mock_session.rollback.assert_awaited_once()


# ============================================================================
# Commit
# ============================================================================


class TestUnitOfWorkCommit:
    """Tests for commit method."""

    async def test_commit_delegates_to_session_commit(
        self, mock_session: AsyncMock
    ) -> None:
        """Test commit() calls session.commit() to persist all changes atomically."""
        uow = UnitOfWork(mock_session)

        await uow.commit()

        mock_session.commit.assert_awaited_once()


# ============================================================================
# Rollback
# ============================================================================


class TestUnitOfWorkRollback:
    """Tests for rollback method."""

    async def test_rollback_delegates_to_session_rollback(
        self, mock_session: AsyncMock
    ) -> None:
        """Test rollback() calls session.rollback() to discard all changes."""
        uow = UnitOfWork(mock_session)

        await uow.rollback()

        mock_session.rollback.assert_awaited_once()
