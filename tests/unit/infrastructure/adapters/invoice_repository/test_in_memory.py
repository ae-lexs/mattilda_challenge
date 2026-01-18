"""Unit tests for InMemoryInvoiceRepository.

These tests verify the in-memory repository implementation used for
unit testing use cases. While this is test infrastructure, it contains
non-trivial logic (filtering, sorting, pagination) that could have bugs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from mattilda_challenge.application.common import Page, PaginationParams, SortParams
from mattilda_challenge.application.filters import InvoiceFilters
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    StudentId,
)
from mattilda_challenge.infrastructure.adapters.invoice_repository import (
    InMemoryInvoiceRepository,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def repository() -> InMemoryInvoiceRepository:
    """Provide fresh in-memory repository for each test."""
    return InMemoryInvoiceRepository()


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def standard_late_fee_policy() -> LateFeePolicy:
    """Provide standard late fee policy for testing."""
    return LateFeePolicy(monthly_rate=Decimal("0.05"))


@pytest.fixture
def student_id_1() -> StudentId:
    """Provide first student ID for testing."""
    return StudentId(value=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))


@pytest.fixture
def student_id_2() -> StudentId:
    """Provide second student ID for testing."""
    return StudentId(value=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))


@pytest.fixture
def invoice_1(
    student_id_1: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Create first test invoice."""
    return Invoice(
        id=InvoiceId(value=UUID("11111111-1111-1111-1111-111111111111")),
        student_id=student_id_1,
        invoice_number="INV-2024-000001",
        amount=Decimal("1000.00"),
        due_date=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
        description="Invoice 1",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PENDING,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def invoice_2(
    student_id_1: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Create second test invoice (same student, different amount)."""
    return Invoice(
        id=InvoiceId(value=UUID("22222222-2222-2222-2222-222222222222")),
        student_id=student_id_1,
        invoice_number="INV-2024-000002",
        amount=Decimal("500.00"),
        due_date=datetime(2024, 3, 1, 0, 0, 0, tzinfo=UTC),
        description="Invoice 2",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PARTIALLY_PAID,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def invoice_3(
    student_id_2: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Create third test invoice (different student)."""
    return Invoice(
        id=InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333")),
        student_id=student_id_2,
        invoice_number="INV-2024-000003",
        amount=Decimal("750.00"),
        due_date=datetime(2024, 1, 20, 0, 0, 0, tzinfo=UTC),
        description="Invoice 3",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PAID,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


# ============================================================================
# Basic Operations
# ============================================================================


class TestInMemoryInvoiceRepositorySave:
    """Tests for save method."""

    async def test_save_stores_invoice(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
    ) -> None:
        """Test save stores invoice in repository."""
        result = await repository.save(invoice_1)

        assert result == invoice_1
        assert await repository.get_by_id(invoice_1.id) == invoice_1

    async def test_save_returns_same_invoice(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
    ) -> None:
        """Test save returns the saved invoice."""
        result = await repository.save(invoice_1)

        assert result is invoice_1

    async def test_save_overwrites_existing(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        fixed_time: datetime,
        standard_late_fee_policy: LateFeePolicy,
        student_id_1: StudentId,
    ) -> None:
        """Test save overwrites existing invoice with same ID."""
        await repository.save(invoice_1)

        updated_invoice = Invoice(
            id=invoice_1.id,
            student_id=student_id_1,
            invoice_number="INV-2024-000001",
            amount=Decimal("2000.00"),  # Changed
            due_date=datetime(2024, 2, 1, 0, 0, 0, tzinfo=UTC),
            description="Updated invoice",
            late_fee_policy=standard_late_fee_policy,
            status=InvoiceStatus.PAID,  # Changed
            created_at=fixed_time,
            updated_at=fixed_time,
        )

        await repository.save(updated_invoice)
        fetched = await repository.get_by_id(invoice_1.id)

        assert fetched is not None
        assert fetched.amount == Decimal("2000.00")
        assert fetched.status == InvoiceStatus.PAID


class TestInMemoryInvoiceRepositoryGetById:
    """Tests for get_by_id method."""

    async def test_get_by_id_returns_invoice(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
    ) -> None:
        """Test get_by_id returns stored invoice."""
        await repository.save(invoice_1)

        result = await repository.get_by_id(invoice_1.id)

        assert result == invoice_1

    async def test_get_by_id_returns_none_when_not_found(
        self,
        repository: InMemoryInvoiceRepository,
    ) -> None:
        """Test get_by_id returns None for non-existent ID."""
        non_existent_id = InvoiceId(value=UUID("99999999-9999-9999-9999-999999999999"))

        result = await repository.get_by_id(non_existent_id)

        assert result is None

    async def test_get_by_id_accepts_for_update_parameter(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
    ) -> None:
        """Test get_by_id accepts for_update parameter (ignored in memory)."""
        await repository.save(invoice_1)

        result = await repository.get_by_id(invoice_1.id, for_update=True)

        assert result == invoice_1


# ============================================================================
# Filtering
# ============================================================================


class TestInMemoryInvoiceRepositoryFindFilters:
    """Tests for find method filtering."""

    async def test_find_returns_all_without_filters(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find returns all invoices when no filters applied."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 3

    async def test_find_filters_by_student_id(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
        student_id_1: StudentId,
    ) -> None:
        """Test find filters by student_id correctly."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(student_id=student_id_1.value),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 2
        for invoice in result.items:
            assert invoice.student_id == student_id_1

    async def test_find_filters_by_status(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find filters by status correctly."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(status="pending"),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert result.items[0].status == InvoiceStatus.PENDING

    async def test_find_filters_by_due_date_from(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find filters by due_date_from correctly."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        # invoice_1: 2024-02-01, invoice_2: 2024-03-01, invoice_3: 2024-01-20
        result = await repository.find(
            filters=InvoiceFilters(due_date_from=datetime(2024, 2, 1, tzinfo=UTC)),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="due_date", sort_order="asc"),
        )

        assert result.total == 2
        for invoice in result.items:
            assert invoice.due_date >= datetime(2024, 2, 1, tzinfo=UTC)

    async def test_find_filters_by_due_date_to(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find filters by due_date_to correctly."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(due_date_to=datetime(2024, 2, 1, tzinfo=UTC)),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="due_date", sort_order="asc"),
        )

        assert result.total == 2
        for invoice in result.items:
            assert invoice.due_date <= datetime(2024, 2, 1, tzinfo=UTC)

    async def test_find_filters_by_due_date_range(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find filters by due_date range correctly."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(
                due_date_from=datetime(2024, 1, 25, tzinfo=UTC),
                due_date_to=datetime(2024, 2, 15, tzinfo=UTC),
            ),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="due_date", sort_order="asc"),
        )

        # Only invoice_1 (2024-02-01) falls in range [2024-01-25, 2024-02-15]
        assert result.total == 1
        assert result.items[0].id == invoice_1.id

    async def test_find_multiple_filters_combined(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
        student_id_1: StudentId,
    ) -> None:
        """Test find combines multiple filters with AND logic."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(
                student_id=student_id_1.value,
                status="pending",
            ),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        # Only invoice_1 matches both criteria
        assert result.total == 1
        assert result.items[0].id == invoice_1.id


# ============================================================================
# Sorting
# ============================================================================


class TestInMemoryInvoiceRepositoryFindSorting:
    """Tests for find method sorting."""

    async def test_find_sorts_by_amount_ascending(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find sorts by amount ascending."""
        repository.add(invoice_1)  # 1000.00
        repository.add(invoice_2)  # 500.00
        repository.add(invoice_3)  # 750.00

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        amounts = [inv.amount for inv in result.items]
        assert amounts == sorted(amounts)
        assert amounts == [Decimal("500.00"), Decimal("750.00"), Decimal("1000.00")]

    async def test_find_sorts_by_amount_descending(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find sorts by amount descending."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="amount", sort_order="desc"),
        )

        amounts = [inv.amount for inv in result.items]
        assert amounts == sorted(amounts, reverse=True)

    async def test_find_sorts_by_due_date_ascending(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find sorts by due_date ascending."""
        repository.add(invoice_1)  # 2024-02-01
        repository.add(invoice_2)  # 2024-03-01
        repository.add(invoice_3)  # 2024-01-20

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="due_date", sort_order="asc"),
        )

        dates = [inv.due_date for inv in result.items]
        assert dates == sorted(dates)

    async def test_find_sorts_by_due_date_descending(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find sorts by due_date descending."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="due_date", sort_order="desc"),
        )

        dates = [inv.due_date for inv in result.items]
        assert dates == sorted(dates, reverse=True)

    async def test_find_sorts_by_status(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find sorts by status."""
        repository.add(invoice_1)  # pending
        repository.add(invoice_2)  # partially_paid
        repository.add(invoice_3)  # paid

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="status", sort_order="asc"),
        )

        statuses = [inv.status.value for inv in result.items]
        assert statuses == sorted(statuses)

    async def test_find_defaults_to_created_at_for_unknown_sort(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
    ) -> None:
        """Test find defaults to created_at for unknown sort field."""
        repository.add(invoice_1)

        # Should not raise, falls back to created_at
        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="unknown_field", sort_order="asc"),
        )

        assert len(result.items) == 1


# ============================================================================
# Pagination
# ============================================================================


class TestInMemoryInvoiceRepositoryFindPagination:
    """Tests for find method pagination."""

    async def test_find_respects_offset(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find respects pagination offset."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=1, limit=10),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2  # Skipped first one
        assert result.offset == 1

    async def test_find_respects_limit(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find respects pagination limit."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=2),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.limit == 2

    async def test_find_returns_correct_total(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
    ) -> None:
        """Test find returns correct total count regardless of pagination."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=1),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 1

    async def test_find_offset_beyond_results(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
    ) -> None:
        """Test find returns empty when offset exceeds total."""
        repository.add(invoice_1)

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=10, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 1
        assert len(result.items) == 0

    async def test_find_returns_page_object(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
    ) -> None:
        """Test find returns Page object with correct structure."""
        repository.add(invoice_1)

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert isinstance(result, Page)
        assert isinstance(result.items, tuple)
        assert result.offset == 0
        assert result.limit == 10


# ============================================================================
# Convenience Methods
# ============================================================================


class TestInMemoryInvoiceRepositoryFindByStudent:
    """Tests for find_by_student convenience method."""

    async def test_find_by_student_returns_student_invoices(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
        student_id_1: StudentId,
    ) -> None:
        """Test find_by_student returns only invoices for specified student."""
        repository.add(invoice_1)
        repository.add(invoice_2)
        repository.add(invoice_3)

        result = await repository.find_by_student(
            student_id=student_id_1,
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 2
        for invoice in result.items:
            assert invoice.student_id == student_id_1

    async def test_find_by_student_returns_empty_for_no_invoices(
        self,
        repository: InMemoryInvoiceRepository,
    ) -> None:
        """Test find_by_student returns empty for student with no invoices."""
        no_invoice_student = StudentId(
            value=UUID("99999999-9999-9999-9999-999999999999")
        )

        result = await repository.find_by_student(
            student_id=no_invoice_student,
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 0
        assert len(result.items) == 0


class TestInMemoryInvoiceRepositoryGetTotalAmountByStudent:
    """Tests for get_total_amount_by_student method."""

    async def test_returns_sum_of_invoice_amounts(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
        invoice_3: Invoice,
        student_id_1: StudentId,
    ) -> None:
        """Test get_total_amount_by_student returns correct sum."""
        repository.add(invoice_1)  # 1000.00 - student_id_1
        repository.add(invoice_2)  # 500.00 - student_id_1
        repository.add(invoice_3)  # 750.00 - student_id_2

        result = await repository.get_total_amount_by_student(student_id_1)

        assert result == Decimal("1500.00")
        assert isinstance(result, Decimal)

    async def test_returns_zero_for_student_with_no_invoices(
        self,
        repository: InMemoryInvoiceRepository,
    ) -> None:
        """Test get_total_amount_by_student returns 0 for no invoices."""
        no_invoice_student = StudentId(
            value=UUID("99999999-9999-9999-9999-999999999999")
        )

        result = await repository.get_total_amount_by_student(no_invoice_student)

        assert result == Decimal("0")
        assert isinstance(result, Decimal)


# ============================================================================
# Test Helper Methods
# ============================================================================


class TestInMemoryInvoiceRepositoryHelpers:
    """Tests for test helper methods."""

    async def test_add_stores_invoice_directly(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
    ) -> None:
        """Test add() stores invoice without async."""
        repository.add(invoice_1)

        result = await repository.get_by_id(invoice_1.id)

        assert result == invoice_1

    async def test_clear_removes_all_invoices(
        self,
        repository: InMemoryInvoiceRepository,
        invoice_1: Invoice,
        invoice_2: Invoice,
    ) -> None:
        """Test clear() removes all stored invoices."""
        repository.add(invoice_1)
        repository.add(invoice_2)

        repository.clear()

        assert await repository.get_by_id(invoice_1.id) is None
        assert await repository.get_by_id(invoice_2.id) is None

        result = await repository.find(
            filters=InvoiceFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )
        assert result.total == 0
