"""Unit tests for InMemoryPaymentRepository.

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
from mattilda_challenge.application.filters import PaymentFilters
from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId, StudentId
from mattilda_challenge.infrastructure.adapters.payment_repository import (
    InMemoryPaymentRepository,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def repository() -> InMemoryPaymentRepository:
    """Provide fresh in-memory repository for each test."""
    return InMemoryPaymentRepository()


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def invoice_id_1() -> InvoiceId:
    """Provide first invoice ID for testing."""
    return InvoiceId(value=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"))


@pytest.fixture
def invoice_id_2() -> InvoiceId:
    """Provide second invoice ID for testing."""
    return InvoiceId(value=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))


@pytest.fixture
def student_id_1() -> StudentId:
    """Provide first student ID for testing."""
    return StudentId(value=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"))


@pytest.fixture
def student_id_2() -> StudentId:
    """Provide second student ID for testing."""
    return StudentId(value=UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"))


@pytest.fixture
def payment_1(invoice_id_1: InvoiceId, fixed_time: datetime) -> Payment:
    """Create first test payment."""
    return Payment(
        id=PaymentId(value=UUID("11111111-1111-1111-1111-111111111111")),
        invoice_id=invoice_id_1,
        amount=Decimal("500.00"),
        payment_date=fixed_time,
        payment_method="bank_transfer",
        reference_number="REF-001",
        created_at=fixed_time,
    )


@pytest.fixture
def payment_2(invoice_id_1: InvoiceId, fixed_time: datetime) -> Payment:
    """Create second test payment (same invoice)."""
    return Payment(
        id=PaymentId(value=UUID("22222222-2222-2222-2222-222222222222")),
        invoice_id=invoice_id_1,
        amount=Decimal("300.00"),
        payment_date=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
        payment_method="cash",
        reference_number=None,
        created_at=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC),
    )


@pytest.fixture
def payment_3(invoice_id_2: InvoiceId, fixed_time: datetime) -> Payment:
    """Create third test payment (different invoice)."""
    return Payment(
        id=PaymentId(value=UUID("33333333-3333-3333-3333-333333333333")),
        invoice_id=invoice_id_2,
        amount=Decimal("1000.00"),
        payment_date=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
        payment_method="card",
        reference_number="REF-003",
        created_at=datetime(2024, 1, 17, 12, 0, 0, tzinfo=UTC),
    )


# ============================================================================
# Basic Operations
# ============================================================================


class TestInMemoryPaymentRepositorySave:
    """Tests for save method."""

    async def test_save_stores_payment(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
    ) -> None:
        """Test save stores payment in repository."""
        result = await repository.save(payment_1)

        assert result == payment_1
        assert await repository.get_by_id(payment_1.id) == payment_1

    async def test_save_returns_same_payment(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
    ) -> None:
        """Test save returns the saved payment."""
        result = await repository.save(payment_1)

        assert result is payment_1


class TestInMemoryPaymentRepositoryGetById:
    """Tests for get_by_id method."""

    async def test_get_by_id_returns_payment(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
    ) -> None:
        """Test get_by_id returns stored payment."""
        await repository.save(payment_1)

        result = await repository.get_by_id(payment_1.id)

        assert result == payment_1

    async def test_get_by_id_returns_none_when_not_found(
        self,
        repository: InMemoryPaymentRepository,
    ) -> None:
        """Test get_by_id returns None for non-existent ID."""
        non_existent_id = PaymentId(value=UUID("99999999-9999-9999-9999-999999999999"))

        result = await repository.get_by_id(non_existent_id)

        assert result is None

    async def test_get_by_id_accepts_for_update_parameter(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
    ) -> None:
        """Test get_by_id accepts for_update parameter (ignored in memory)."""
        await repository.save(payment_1)

        result = await repository.get_by_id(payment_1.id, for_update=True)

        assert result == payment_1


# ============================================================================
# Special Methods
# ============================================================================


class TestInMemoryPaymentRepositoryGetTotalByInvoice:
    """Tests for get_total_by_invoice method."""

    async def test_returns_sum_of_payment_amounts(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
        invoice_id_1: InvoiceId,
    ) -> None:
        """Test get_total_by_invoice returns correct sum."""
        repository.add(payment_1)  # 500.00 - invoice_id_1
        repository.add(payment_2)  # 300.00 - invoice_id_1
        repository.add(payment_3)  # 1000.00 - invoice_id_2

        result = await repository.get_total_by_invoice(invoice_id_1)

        assert result == Decimal("800.00")
        assert isinstance(result, Decimal)

    async def test_returns_zero_for_invoice_with_no_payments(
        self,
        repository: InMemoryPaymentRepository,
    ) -> None:
        """Test get_total_by_invoice returns 0 for no payments."""
        no_payment_invoice = InvoiceId(
            value=UUID("88888888-8888-8888-8888-888888888888")
        )

        result = await repository.get_total_by_invoice(no_payment_invoice)

        assert result == Decimal("0")
        assert isinstance(result, Decimal)


class TestInMemoryPaymentRepositoryGetTotalByStudent:
    """Tests for get_total_by_student method."""

    async def test_returns_sum_for_student_with_mapping(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
        invoice_id_1: InvoiceId,
        invoice_id_2: InvoiceId,
        student_id_1: StudentId,
        student_id_2: StudentId,
    ) -> None:
        """Test get_total_by_student returns correct sum when mapping is set."""
        repository.add(payment_1)  # 500.00 - invoice_id_1
        repository.add(payment_2)  # 300.00 - invoice_id_1
        repository.add(payment_3)  # 1000.00 - invoice_id_2

        # Set up invoice->student mapping
        repository.set_invoice_student_mapping(invoice_id_1, student_id_1)
        repository.set_invoice_student_mapping(invoice_id_2, student_id_2)

        result = await repository.get_total_by_student(student_id_1)

        assert result == Decimal("800.00")
        assert isinstance(result, Decimal)

    async def test_returns_zero_for_student_with_no_payments(
        self,
        repository: InMemoryPaymentRepository,
    ) -> None:
        """Test get_total_by_student returns 0 for student with no payments."""
        no_payment_student = StudentId(
            value=UUID("88888888-8888-8888-8888-888888888888")
        )

        result = await repository.get_total_by_student(no_payment_student)

        assert result == Decimal("0")
        assert isinstance(result, Decimal)


class TestInMemoryPaymentRepositoryFindByInvoice:
    """Tests for find_by_invoice convenience method."""

    async def test_find_by_invoice_returns_invoice_payments(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
        invoice_id_1: InvoiceId,
    ) -> None:
        """Test find_by_invoice returns only payments for specified invoice."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find_by_invoice(
            invoice_id=invoice_id_1,
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 2
        for payment in result.items:
            assert payment.invoice_id == invoice_id_1

    async def test_find_by_invoice_returns_empty_for_no_payments(
        self,
        repository: InMemoryPaymentRepository,
    ) -> None:
        """Test find_by_invoice returns empty for invoice with no payments."""
        no_payment_invoice = InvoiceId(
            value=UUID("99999999-9999-9999-9999-999999999999")
        )

        result = await repository.find_by_invoice(
            invoice_id=no_payment_invoice,
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 0
        assert len(result.items) == 0


# ============================================================================
# Filtering
# ============================================================================


class TestInMemoryPaymentRepositoryFindFilters:
    """Tests for find method filtering."""

    async def test_find_returns_all_without_filters(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find returns all payments when no filters applied."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 3

    async def test_find_filters_by_invoice_id(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
        invoice_id_1: InvoiceId,
    ) -> None:
        """Test find filters by invoice_id correctly."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find(
            filters=PaymentFilters(invoice_id=invoice_id_1.value),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 2
        for payment in result.items:
            assert payment.invoice_id == invoice_id_1

    async def test_find_filters_by_payment_date_from(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find filters by payment_date_from correctly."""
        repository.add(payment_1)  # 2024-01-15
        repository.add(payment_2)  # 2024-01-16
        repository.add(payment_3)  # 2024-01-17

        result = await repository.find(
            filters=PaymentFilters(
                payment_date_from=datetime(2024, 1, 16, 0, 0, 0, tzinfo=UTC)
            ),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="payment_date", sort_order="asc"),
        )

        assert result.total == 2
        for payment in result.items:
            assert payment.payment_date >= datetime(2024, 1, 16, 0, 0, 0, tzinfo=UTC)

    async def test_find_filters_by_payment_date_to(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find filters by payment_date_to correctly."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find(
            filters=PaymentFilters(
                payment_date_to=datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC)
            ),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="payment_date", sort_order="asc"),
        )

        assert result.total == 2
        for payment in result.items:
            assert payment.payment_date <= datetime(2024, 1, 16, 12, 0, 0, tzinfo=UTC)

    async def test_find_filters_by_date_range(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find filters by payment date range correctly."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find(
            filters=PaymentFilters(
                payment_date_from=datetime(2024, 1, 16, 0, 0, 0, tzinfo=UTC),
                payment_date_to=datetime(2024, 1, 16, 23, 59, 59, tzinfo=UTC),
            ),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="payment_date", sort_order="asc"),
        )

        # Only payment_2 (2024-01-16) falls in range
        assert result.total == 1
        assert result.items[0].id == payment_2.id


# ============================================================================
# Sorting
# ============================================================================


class TestInMemoryPaymentRepositoryFindSorting:
    """Tests for find method sorting."""

    async def test_find_sorts_by_amount_ascending(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find sorts by amount ascending."""
        repository.add(payment_1)  # 500.00
        repository.add(payment_2)  # 300.00
        repository.add(payment_3)  # 1000.00

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        amounts = [p.amount for p in result.items]
        assert amounts == [Decimal("300.00"), Decimal("500.00"), Decimal("1000.00")]

    async def test_find_sorts_by_amount_descending(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find sorts by amount descending."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="amount", sort_order="desc"),
        )

        amounts = [p.amount for p in result.items]
        assert amounts == sorted(amounts, reverse=True)

    async def test_find_sorts_by_payment_date_ascending(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find sorts by payment_date ascending."""
        repository.add(payment_1)  # 2024-01-15
        repository.add(payment_2)  # 2024-01-16
        repository.add(payment_3)  # 2024-01-17

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="payment_date", sort_order="asc"),
        )

        dates = [p.payment_date for p in result.items]
        assert dates == sorted(dates)

    async def test_find_sorts_by_created_at_descending(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find sorts by created_at descending."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        dates = [p.created_at for p in result.items]
        assert dates == sorted(dates, reverse=True)


# ============================================================================
# Pagination
# ============================================================================


class TestInMemoryPaymentRepositoryFindPagination:
    """Tests for find method pagination."""

    async def test_find_respects_offset(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find respects pagination offset."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=1, limit=10),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.offset == 1

    async def test_find_respects_limit(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find respects pagination limit."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=2),
            sort=SortParams(sort_by="amount", sort_order="asc"),
        )

        assert result.total == 3
        assert len(result.items) == 2
        assert result.limit == 2

    async def test_find_returns_correct_total(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
        payment_3: Payment,
    ) -> None:
        """Test find returns correct total count regardless of pagination."""
        repository.add(payment_1)
        repository.add(payment_2)
        repository.add(payment_3)

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=1),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert result.total == 3
        assert len(result.items) == 1

    async def test_find_returns_page_object(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
    ) -> None:
        """Test find returns Page object with correct structure."""
        repository.add(payment_1)

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )

        assert isinstance(result, Page)
        assert isinstance(result.items, tuple)
        assert result.offset == 0
        assert result.limit == 10


# ============================================================================
# Test Helper Methods
# ============================================================================


class TestInMemoryPaymentRepositoryHelpers:
    """Tests for test helper methods."""

    async def test_add_stores_payment_directly(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
    ) -> None:
        """Test add() stores payment without async."""
        repository.add(payment_1)

        result = await repository.get_by_id(payment_1.id)

        assert result == payment_1

    async def test_clear_removes_all_payments(
        self,
        repository: InMemoryPaymentRepository,
        payment_1: Payment,
        payment_2: Payment,
    ) -> None:
        """Test clear() removes all stored payments."""
        repository.add(payment_1)
        repository.add(payment_2)

        repository.clear()

        assert await repository.get_by_id(payment_1.id) is None
        assert await repository.get_by_id(payment_2.id) is None

        result = await repository.find(
            filters=PaymentFilters(),
            pagination=PaginationParams(offset=0, limit=10),
            sort=SortParams(sort_by="created_at", sort_order="desc"),
        )
        assert result.total == 0

    async def test_clear_removes_invoice_student_mappings(
        self,
        repository: InMemoryPaymentRepository,
        invoice_id_1: InvoiceId,
        student_id_1: StudentId,
    ) -> None:
        """Test clear() also removes invoice->student mappings."""
        repository.set_invoice_student_mapping(invoice_id_1, student_id_1)
        repository.clear()

        # After clear, mapping should be gone
        result = await repository.get_total_by_student(student_id_1)
        assert result == Decimal("0")

    def test_set_invoice_student_mapping(
        self,
        repository: InMemoryPaymentRepository,
        invoice_id_1: InvoiceId,
        student_id_1: StudentId,
    ) -> None:
        """Test set_invoice_student_mapping stores mapping."""
        repository.set_invoice_student_mapping(invoice_id_1, student_id_1)

        # Mapping should be stored (verified through get_total_by_student behavior)
        assert invoice_id_1 in repository._invoice_to_student
        assert repository._invoice_to_student[invoice_id_1] == student_id_1
