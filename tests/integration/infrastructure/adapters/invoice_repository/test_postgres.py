"""Integration tests for PostgresInvoiceRepository.

These tests verify the PostgreSQL repository implementation against a real database.
Per ADR-009, integration tests are required for:
- All repository methods
- Cross-aggregate filters (school_id on invoices requires join through Student)
- Database-specific behavior (transactions, locks, constraints)
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import InvoiceFilters
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
    StudentModel,
)

pytestmark = pytest.mark.integration


class TestPostgresInvoiceRepositoryGetById:
    """Integration tests for get_by_id method."""

    async def test_returns_invoice_when_exists(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
        fixed_invoice_id: InvoiceId,
    ) -> None:
        """Test get_by_id returns invoice when it exists."""
        result = await invoice_repository.get_by_id(fixed_invoice_id)

        assert result is not None
        assert result.id == fixed_invoice_id
        assert result.amount == Decimal("1000.00")
        assert result.status == InvoiceStatus.PENDING

    async def test_returns_none_when_not_found(
        self,
        invoice_repository: PostgresInvoiceRepository,
    ) -> None:
        """Test get_by_id returns None for non-existent ID."""
        non_existent_id = InvoiceId(value=UUID("99999999-9999-9999-9999-999999999999"))

        result = await invoice_repository.get_by_id(non_existent_id)

        assert result is None

    async def test_returns_correct_entity_fields(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
        fixed_invoice_id: InvoiceId,
        fixed_student_id: StudentId,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """Test get_by_id returns entity with all fields correctly mapped."""
        result = await invoice_repository.get_by_id(fixed_invoice_id)

        assert result is not None
        assert result.id == fixed_invoice_id
        assert result.student_id == fixed_student_id
        assert result.invoice_number == "INV-2024-000001"
        assert result.amount == Decimal("1000.00")
        assert result.due_date == datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC)
        assert result.description == "Tuition fee for January 2024"
        assert (
            result.late_fee_policy.monthly_rate == standard_late_fee_policy.monthly_rate
        )
        assert result.status == InvoiceStatus.PENDING

    async def test_for_update_parameter_accepted(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
        fixed_invoice_id: InvoiceId,
    ) -> None:
        """Test get_by_id accepts for_update parameter (row locking)."""
        # This test verifies the SQL executes without error
        # Full lock testing requires concurrent transactions
        result = await invoice_repository.get_by_id(fixed_invoice_id, for_update=True)

        assert result is not None
        assert result.id == fixed_invoice_id


class TestPostgresInvoiceRepositorySave:
    """Integration tests for save method."""

    async def test_save_inserts_new_invoice(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_student: StudentModel,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """Test save inserts a new invoice into the database."""
        new_invoice_id = InvoiceId(value=UUID("ffffffff-ffff-ffff-ffff-ffffffffffff"))
        invoice = Invoice(
            id=new_invoice_id,
            student_id=StudentId(value=saved_student.id),
            invoice_number="INV-2024-NEW001",
            amount=Decimal("2000.00"),
            due_date=datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC),
            description="New tuition fee",
            late_fee_policy=standard_late_fee_policy,
            status=InvoiceStatus.PENDING,
            created_at=fixed_time,
            updated_at=fixed_time,
        )

        result = await invoice_repository.save(invoice)

        assert result.id == new_invoice_id
        assert result.amount == Decimal("2000.00")

        # Verify it's in the database
        fetched = await invoice_repository.get_by_id(new_invoice_id)
        assert fetched is not None
        assert fetched.amount == Decimal("2000.00")

    async def test_save_updates_existing_invoice(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
        fixed_invoice_id: InvoiceId,
        fixed_student_id: StudentId,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """Test save updates an existing invoice (upsert behavior)."""
        updated_time = datetime(2024, 1, 20, 12, 0, 0, tzinfo=UTC)
        updated_invoice = Invoice(
            id=fixed_invoice_id,
            student_id=fixed_student_id,
            invoice_number="INV-2024-000001",
            amount=Decimal("1000.00"),
            due_date=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
            description="Tuition fee for January 2024",
            late_fee_policy=standard_late_fee_policy,
            status=InvoiceStatus.PARTIALLY_PAID,  # Changed status
            created_at=fixed_time,
            updated_at=updated_time,
        )

        result = await invoice_repository.save(updated_invoice)

        assert result.status == InvoiceStatus.PARTIALLY_PAID
        assert result.updated_at == updated_time

        # Verify the update persisted
        fetched = await invoice_repository.get_by_id(fixed_invoice_id)
        assert fetched is not None
        assert fetched.status == InvoiceStatus.PARTIALLY_PAID

    async def test_save_preserves_decimal_precision(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_student: StudentModel,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """Test save preserves Decimal precision (NUMERIC(12,2))."""
        precise_amount = Decimal("1234.56")
        invoice_id = InvoiceId(value=UUID("12345678-1234-1234-1234-123456789012"))
        invoice = Invoice(
            id=invoice_id,
            student_id=StudentId(value=saved_student.id),
            invoice_number="INV-2024-PRECISE",
            amount=precise_amount,
            due_date=datetime(2024, 5, 1, 0, 0, 0, tzinfo=UTC),
            description="Precision test",
            late_fee_policy=standard_late_fee_policy,
            status=InvoiceStatus.PENDING,
            created_at=fixed_time,
            updated_at=fixed_time,
        )

        await invoice_repository.save(invoice)
        fetched = await invoice_repository.get_by_id(invoice_id)

        assert fetched is not None
        assert fetched.amount == precise_amount
        assert str(fetched.amount) == "1234.56"


class TestPostgresInvoiceRepositoryFind:
    """Integration tests for find method with filters."""

    async def test_find_returns_all_invoices_without_filters(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
    ) -> None:
        """Test find returns all invoices when no filters applied."""
        result = await invoice_repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert isinstance(result, Page)
        assert result.total >= 1
        assert len(result.items) >= 1

    async def test_find_filters_by_student_id(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
        fixed_student_id: StudentId,
    ) -> None:
        """Test find filters by student_id correctly."""
        result = await invoice_repository.find(
            filters=InvoiceFilters(student_id=fixed_student_id.value),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total >= 1
        for invoice in result.items:
            assert invoice.student_id == fixed_student_id

    async def test_find_filters_by_status(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
    ) -> None:
        """Test find filters by status correctly."""
        result = await invoice_repository.find(
            filters=InvoiceFilters(status="pending"),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total >= 1
        for invoice in result.items:
            assert invoice.status == InvoiceStatus.PENDING

    async def test_find_filters_by_due_date_range(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
    ) -> None:
        """Test find filters by due_date range correctly."""
        result = await invoice_repository.find(
            filters=InvoiceFilters(
                due_date_from=datetime(2024, 1, 1, tzinfo=UTC).date(),
                due_date_to=datetime(2024, 12, 31, tzinfo=UTC).date(),
            ),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="due_date", sort_order="asc"),
        )

        assert result.total >= 1
        for invoice in result.items:
            assert invoice.due_date >= datetime(2024, 1, 1, tzinfo=UTC)
            assert invoice.due_date <= datetime(2024, 12, 31, 23, 59, 59, tzinfo=UTC)

    async def test_find_filters_by_school_id_cross_aggregate(
        self,
        db_session: AsyncSession,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
        saved_student_2: StudentModel,
        fixed_school_id: SchoolId,
        fixed_school_id_2: SchoolId,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """
        Test find filters by school_id (cross-aggregate filter).

        CRITICAL: This is a cross-aggregate filter that requires joining
        through the Student table. Per ADR-009, this MUST be integration tested.
        """
        # Create invoice for student in school 2
        invoice_school_2 = InvoiceModel(
            id=UUID("77777777-7777-7777-7777-777777777777"),
            student_id=saved_student_2.id,
            invoice_number="INV-2024-SCHOOL2",
            amount=Decimal("800.00"),
            due_date=datetime(2024, 2, 15, 0, 0, 0, tzinfo=UTC),
            description="Invoice for school 2 student",
            late_fee_policy_monthly_rate=standard_late_fee_policy.monthly_rate,
            status="pending",
            created_at=fixed_time,
            updated_at=fixed_time,
        )
        db_session.add(invoice_school_2)
        await db_session.flush()

        # Filter by school 1 - should only get invoice from school 1
        result_school_1 = await invoice_repository.find(
            filters=InvoiceFilters(school_id=fixed_school_id.value),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        # Filter by school 2 - should only get invoice from school 2
        result_school_2 = await invoice_repository.find(
            filters=InvoiceFilters(school_id=fixed_school_id_2.value),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        # Verify school 1 results
        assert result_school_1.total >= 1
        assert all(
            inv.student_id.value != saved_student_2.id for inv in result_school_1.items
        )

        # Verify school 2 results
        assert result_school_2.total >= 1
        assert all(
            inv.student_id.value == saved_student_2.id for inv in result_school_2.items
        )


class TestPostgresInvoiceRepositoryFindPagination:
    """Integration tests for find method pagination."""

    async def test_find_respects_offset(
        self,
        db_session: AsyncSession,
        invoice_repository: PostgresInvoiceRepository,
        saved_student: StudentModel,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """Test find respects pagination offset."""
        # Create multiple invoices
        # Note: due_date must be after created_at (fixed_time = 2024-01-15)
        for i in range(5):
            invoice = InvoiceModel(
                id=UUID(f"1000000{i}-0000-0000-0000-000000000000"),
                student_id=saved_student.id,
                invoice_number=f"INV-2024-PAG{i:03d}",
                amount=Decimal(f"{100 * (i + 1)}.00"),
                due_date=datetime(
                    2024, i + 2, 1, 0, 0, 0, tzinfo=UTC
                ),  # Start from Feb
                description=f"Pagination test invoice {i}",
                late_fee_policy_monthly_rate=standard_late_fee_policy.monthly_rate,
                status="pending",
                created_at=fixed_time,
                updated_at=fixed_time,
            )
            db_session.add(invoice)
        await db_session.flush()

        # Get first page
        page_1 = await invoice_repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=2),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        # Get second page
        page_2 = await invoice_repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=2, limit=2),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        assert len(page_1.items) == 2
        assert len(page_2.items) == 2
        # Verify no overlap
        page_1_ids = {inv.id for inv in page_1.items}
        page_2_ids = {inv.id for inv in page_2.items}
        assert page_1_ids.isdisjoint(page_2_ids)

    async def test_find_respects_limit(
        self,
        db_session: AsyncSession,
        invoice_repository: PostgresInvoiceRepository,
        saved_student: StudentModel,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """Test find respects pagination limit."""
        # Create multiple invoices
        for i in range(5):
            invoice = InvoiceModel(
                id=UUID(f"2000000{i}-0000-0000-0000-000000000000"),
                student_id=saved_student.id,
                invoice_number=f"INV-2024-LIM{i:03d}",
                amount=Decimal(f"{100 * (i + 1)}.00"),
                due_date=datetime(2024, i + 1, 1, 0, 0, 0, tzinfo=UTC),
                description=f"Limit test invoice {i}",
                late_fee_policy_monthly_rate=standard_late_fee_policy.monthly_rate,
                status="pending",
                created_at=fixed_time,
                updated_at=fixed_time,
            )
            db_session.add(invoice)
        await db_session.flush()

        result = await invoice_repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=3),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert len(result.items) == 3
        assert result.total >= 5

    async def test_find_returns_correct_total(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
    ) -> None:
        """Test find returns correct total count."""
        result = await invoice_repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=1),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total >= 1
        assert result.offset == 0
        assert result.limit == 1


class TestPostgresInvoiceRepositoryFindSorting:
    """Integration tests for find method sorting."""

    async def test_find_sorts_by_amount_ascending(
        self,
        db_session: AsyncSession,
        invoice_repository: PostgresInvoiceRepository,
        saved_student: StudentModel,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """Test find sorts by amount ascending."""
        amounts = [Decimal("300.00"), Decimal("100.00"), Decimal("200.00")]
        for i, amount in enumerate(amounts):
            invoice = InvoiceModel(
                id=UUID(f"3000000{i}-0000-0000-0000-000000000000"),
                student_id=saved_student.id,
                invoice_number=f"INV-2024-SORT{i:03d}",
                amount=amount,
                due_date=datetime(2024, 6, 1, 0, 0, 0, tzinfo=UTC),
                description=f"Sort test invoice {i}",
                late_fee_policy_monthly_rate=standard_late_fee_policy.monthly_rate,
                status="pending",
                created_at=fixed_time,
                updated_at=fixed_time,
            )
            db_session.add(invoice)
        await db_session.flush()

        result = await invoice_repository.find(
            filters=InvoiceFilters(student_id=saved_student.id),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        amounts_result = [inv.amount for inv in result.items]
        assert amounts_result == sorted(amounts_result)

    async def test_find_sorts_by_due_date_descending(
        self,
        db_session: AsyncSession,
        invoice_repository: PostgresInvoiceRepository,
        saved_student: StudentModel,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """Test find sorts by due_date descending."""
        # Note: due_date must be after created_at (fixed_time = 2024-01-15)
        dates = [
            datetime(2024, 4, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
            datetime(2024, 3, 1, 0, 0, 0, tzinfo=UTC),
        ]
        for i, due_date in enumerate(dates):
            invoice = InvoiceModel(
                id=UUID(f"4000000{i}-0000-0000-0000-000000000000"),
                student_id=saved_student.id,
                invoice_number=f"INV-2024-DATE{i:03d}",
                amount=Decimal("500.00"),
                due_date=due_date,
                description=f"Date sort test invoice {i}",
                late_fee_policy_monthly_rate=standard_late_fee_policy.monthly_rate,
                status="pending",
                created_at=fixed_time,
                updated_at=fixed_time,
            )
            db_session.add(invoice)
        await db_session.flush()

        result = await invoice_repository.find(
            filters=InvoiceFilters(student_id=saved_student.id),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="due_date", sort_order="desc"),
        )

        dates_result = [inv.due_date for inv in result.items]
        assert dates_result == sorted(dates_result, reverse=True)


class TestPostgresInvoiceRepositoryFindByStudent:
    """Integration tests for find_by_student convenience method."""

    async def test_find_by_student_returns_student_invoices(
        self,
        invoice_repository: PostgresInvoiceRepository,
        saved_invoice: InvoiceModel,  # noqa: ARG002 - ensures test data exists
        fixed_student_id: StudentId,
    ) -> None:
        """Test find_by_student returns invoices for specific student."""
        result = await invoice_repository.find_by_student(
            student_id=fixed_student_id,
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total >= 1
        for invoice in result.items:
            assert invoice.student_id == fixed_student_id

    async def test_find_by_student_returns_empty_for_no_invoices(
        self,
        invoice_repository: PostgresInvoiceRepository,
    ) -> None:
        """Test find_by_student returns empty page for student with no invoices."""
        no_invoice_student = StudentId(
            value=UUID("88888888-8888-8888-8888-888888888888")
        )

        result = await invoice_repository.find_by_student(
            student_id=no_invoice_student,
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 0
        assert len(result.items) == 0


class TestPostgresInvoiceRepositoryGetTotalAmountByStudent:
    """Integration tests for get_total_amount_by_student method."""

    async def test_returns_sum_of_invoice_amounts(
        self,
        db_session: AsyncSession,
        invoice_repository: PostgresInvoiceRepository,
        saved_student: StudentModel,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
    ) -> None:
        """Test get_total_amount_by_student returns correct sum."""
        # Create invoices with known amounts
        amounts = [Decimal("100.00"), Decimal("250.50"), Decimal("149.50")]
        for i, amount in enumerate(amounts):
            invoice = InvoiceModel(
                id=UUID(f"5000000{i}-0000-0000-0000-000000000000"),
                student_id=saved_student.id,
                invoice_number=f"INV-2024-SUM{i:03d}",
                amount=amount,
                due_date=datetime(2024, 6, 1, 0, 0, 0, tzinfo=UTC),
                description=f"Sum test invoice {i}",
                late_fee_policy_monthly_rate=standard_late_fee_policy.monthly_rate,
                status="pending",
                created_at=fixed_time,
                updated_at=fixed_time,
            )
            db_session.add(invoice)
        await db_session.flush()

        result = await invoice_repository.get_total_amount_by_student(
            StudentId(value=saved_student.id)
        )

        expected_total = sum(amounts)
        assert result == expected_total
        assert isinstance(result, Decimal)

    async def test_returns_zero_for_student_with_no_invoices(
        self,
        invoice_repository: PostgresInvoiceRepository,
    ) -> None:
        """Test get_total_amount_by_student returns 0 for student with no invoices."""
        no_invoice_student = StudentId(
            value=UUID("88888888-8888-8888-8888-888888888888")
        )

        result = await invoice_repository.get_total_amount_by_student(
            no_invoice_student
        )

        assert result == Decimal("0")
        assert isinstance(result, Decimal)
