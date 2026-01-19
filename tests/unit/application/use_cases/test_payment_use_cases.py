"""Unit tests for Payment use cases.

Tests for RecordPaymentUseCase and ListPaymentsUseCase following the
Arrange-Act-Assert pattern.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from mattilda_challenge.application.common import PaginationParams, SortParams
from mattilda_challenge.application.filters import PaymentFilters
from mattilda_challenge.application.use_cases import (
    ListPaymentsUseCase,
    RecordPaymentUseCase,
)
from mattilda_challenge.application.use_cases.requests import RecordPaymentRequest
from mattilda_challenge.domain.entities import Invoice, Payment
from mattilda_challenge.domain.exceptions import (
    CannotPayCancelledInvoiceError,
    InvoiceNotFoundError,
    PaymentExceedsBalanceError,
)
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    PaymentId,
    StudentId,
)
from mattilda_challenge.infrastructure.adapters import InMemoryUnitOfWork

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def fixed_invoice_id() -> InvoiceId:
    """Provide fixed invoice ID for testing."""
    return InvoiceId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def fixed_payment_id() -> PaymentId:
    """Provide fixed payment ID for testing."""
    return PaymentId(value=UUID("33333333-3333-3333-3333-333333333333"))


@pytest.fixture
def sample_invoice(
    fixed_invoice_id: InvoiceId, fixed_student_id: StudentId, fixed_time: datetime
) -> Invoice:
    """Provide sample invoice entity for testing."""
    return Invoice(
        id=fixed_invoice_id,
        student_id=fixed_student_id,
        invoice_number="INV-2024-000001",
        amount=Decimal("1000.00"),
        due_date=datetime(2024, 2, 15, tzinfo=UTC),
        description="Test Invoice",
        status=InvoiceStatus.PENDING,
        late_fee_policy=LateFeePolicy(monthly_rate=Decimal("0.05")),
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def sample_payment(
    fixed_payment_id: PaymentId,
    fixed_invoice_id: InvoiceId,
    fixed_time: datetime,
) -> Payment:
    """Provide sample payment entity for testing."""
    return Payment(
        id=fixed_payment_id,
        invoice_id=fixed_invoice_id,
        amount=Decimal("500.00"),
        payment_date=fixed_time,
        payment_method="bank_transfer",
        reference_number="REF123",
        created_at=fixed_time,
    )


@pytest.fixture
def uow() -> InMemoryUnitOfWork:
    """Provide fresh InMemoryUnitOfWork for each test."""
    return InMemoryUnitOfWork()


# ============================================================================
# RecordPaymentUseCase
# ============================================================================


class TestRecordPaymentUseCase:
    """Tests for RecordPaymentUseCase."""

    async def test_execute_creates_payment_with_correct_invoice_id(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates payment with the provided invoice ID."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
            reference_number="REF123",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.invoice_id == sample_invoice.id

    async def test_execute_creates_payment_with_correct_amount(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates payment with the provided amount."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.amount == Decimal("500.00")

    async def test_execute_creates_payment_with_correct_payment_date(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates payment with the provided payment date."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        payment_date = datetime(2024, 1, 10, 14, 30, 0, tzinfo=UTC)
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),
            payment_date=payment_date,
            payment_method="bank_transfer",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.payment_date == payment_date

    async def test_execute_creates_payment_with_correct_payment_method(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates payment with the provided payment method."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="cash",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.payment_method == "cash"

    async def test_execute_creates_payment_with_correct_reference_number(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates payment with the provided reference number."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
            reference_number="TXN-2024-001",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.reference_number == "TXN-2024-001"

    async def test_execute_creates_payment_with_correct_timestamp(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates payment with the injected timestamp."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.created_at == fixed_time

    async def test_execute_persists_payment_to_repository(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute persists payment to repository."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        saved = await uow.payments.get_by_id(result.id)
        assert saved is not None
        assert saved.amount == Decimal("500.00")

    async def test_execute_commits_transaction(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute commits the transaction."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        assert uow.committed is True

    async def test_execute_raises_when_invoice_not_found(
        self,
        uow: InMemoryUnitOfWork,
        fixed_invoice_id: InvoiceId,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises InvoiceNotFoundError when invoice doesn't exist."""
        # Arrange
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=fixed_invoice_id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )

        # Act & Assert
        with pytest.raises(InvoiceNotFoundError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(fixed_invoice_id.value) in str(exc_info.value)

    async def test_execute_raises_when_invoice_is_cancelled(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises CannotPayCancelledInvoiceError when invoice is cancelled."""
        # Arrange
        cancelled_invoice = Invoice(
            id=sample_invoice.id,
            student_id=sample_invoice.student_id,
            invoice_number=sample_invoice.invoice_number,
            amount=sample_invoice.amount,
            due_date=sample_invoice.due_date,
            description=sample_invoice.description,
            status=InvoiceStatus.CANCELLED,
            late_fee_policy=sample_invoice.late_fee_policy,
            created_at=sample_invoice.created_at,
            updated_at=sample_invoice.updated_at,
        )
        await uow.invoices.save(cancelled_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=cancelled_invoice.id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )

        # Act & Assert
        with pytest.raises(CannotPayCancelledInvoiceError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert str(cancelled_invoice.id.value) in str(exc_info.value)

    async def test_execute_raises_when_payment_exceeds_balance(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute raises PaymentExceedsBalanceError when amount exceeds balance."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("1500.00"),  # Invoice amount is 1000.00
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )

        # Act & Assert
        with pytest.raises(PaymentExceedsBalanceError) as exc_info:
            await use_case.execute(uow, request, fixed_time)

        assert "1500.00" in str(exc_info.value)
        assert "1000.00" in str(exc_info.value)

    async def test_execute_updates_invoice_status_to_paid_when_fully_paid(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute updates invoice status to PAID when fully paid."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("1000.00"),  # Full invoice amount
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        updated_invoice = await uow.invoices.get_by_id(sample_invoice.id)
        assert updated_invoice is not None
        assert updated_invoice.status == InvoiceStatus.PAID

    async def test_execute_updates_invoice_status_to_partially_paid(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute updates invoice status to PARTIALLY_PAID when partial payment."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),  # Half of invoice amount
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )

        # Act
        await use_case.execute(uow, request, fixed_time)

        # Assert
        updated_invoice = await uow.invoices.get_by_id(sample_invoice.id)
        assert updated_invoice is not None
        assert updated_invoice.status == InvoiceStatus.PARTIALLY_PAID

    async def test_execute_allows_multiple_partial_payments(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute allows multiple partial payments until fully paid."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        use_case = RecordPaymentUseCase()

        # First payment
        request1 = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("300.00"),
            payment_date=fixed_time,
            payment_method="cash",
        )
        await use_case.execute(uow, request1, fixed_time)
        uow.reset_tracking()

        # Second payment
        request2 = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("400.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
        )
        await use_case.execute(uow, request2, fixed_time)
        uow.reset_tracking()

        # Act - Final payment
        request3 = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("300.00"),
            payment_date=fixed_time,
            payment_method="card",
        )
        await use_case.execute(uow, request3, fixed_time)

        # Assert
        updated_invoice = await uow.invoices.get_by_id(sample_invoice.id)
        assert updated_invoice is not None
        assert updated_invoice.status == InvoiceStatus.PAID

    async def test_execute_creates_payment_with_null_reference_number(
        self,
        uow: InMemoryUnitOfWork,
        sample_invoice: Invoice,
        fixed_time: datetime,
    ) -> None:
        """Test execute creates payment without reference number when not provided."""
        # Arrange
        await uow.invoices.save(sample_invoice)
        uow.reset_tracking()
        use_case = RecordPaymentUseCase()
        request = RecordPaymentRequest(
            invoice_id=sample_invoice.id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="cash",
            # reference_number not provided
        )

        # Act
        result = await use_case.execute(uow, request, fixed_time)

        # Assert
        assert result.reference_number is None


# ============================================================================
# ListPaymentsUseCase
# ============================================================================


class TestListPaymentsUseCase:
    """Tests for ListPaymentsUseCase."""

    async def test_execute_returns_empty_page_when_no_payments(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns empty page when no payments exist."""
        # Arrange
        use_case = ListPaymentsUseCase()
        filters = PaymentFilters()
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 0
        assert len(result.items) == 0

    async def test_execute_returns_all_payments(
        self,
        uow: InMemoryUnitOfWork,
        fixed_invoice_id: InvoiceId,
        fixed_time: datetime,
    ) -> None:
        """Test execute returns all payments when no filters applied."""
        # Arrange
        payment1 = Payment(
            id=PaymentId(value=UUID("11111111-1111-1111-1111-111111111111")),
            invoice_id=fixed_invoice_id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="cash",
            reference_number=None,
            created_at=fixed_time,
        )
        payment2 = Payment(
            id=PaymentId(value=UUID("22222222-2222-2222-2222-222222222222")),
            invoice_id=fixed_invoice_id,
            amount=Decimal("300.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
            reference_number="REF456",
            created_at=fixed_time,
        )
        await uow.payments.save(payment1)
        await uow.payments.save(payment2)

        use_case = ListPaymentsUseCase()
        filters = PaymentFilters()
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 2
        assert len(result.items) == 2

    async def test_execute_applies_pagination(
        self,
        uow: InMemoryUnitOfWork,
        fixed_invoice_id: InvoiceId,
        fixed_time: datetime,
    ) -> None:
        """Test execute applies pagination correctly."""
        # Arrange
        for i in range(5):
            payment = Payment(
                id=PaymentId.generate(),
                invoice_id=fixed_invoice_id,
                amount=Decimal(f"{(i + 1) * 100}.00"),
                payment_date=fixed_time,
                payment_method="cash",
                reference_number=None,
                created_at=fixed_time,
            )
            await uow.payments.save(payment)

        use_case = ListPaymentsUseCase()
        filters = PaymentFilters()
        pagination = PaginationParams(offset=0, limit=2)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 5
        assert len(result.items) == 2

    async def test_execute_applies_invoice_id_filter(
        self,
        uow: InMemoryUnitOfWork,
        fixed_time: datetime,
    ) -> None:
        """Test execute filters payments by invoice ID."""
        # Arrange
        invoice_id_1 = InvoiceId(value=UUID("11111111-1111-1111-1111-111111111111"))
        invoice_id_2 = InvoiceId(value=UUID("22222222-2222-2222-2222-222222222222"))

        payment1 = Payment(
            id=PaymentId.generate(),
            invoice_id=invoice_id_1,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="cash",
            reference_number=None,
            created_at=fixed_time,
        )
        payment2 = Payment(
            id=PaymentId.generate(),
            invoice_id=invoice_id_2,
            amount=Decimal("300.00"),
            payment_date=fixed_time,
            payment_method="bank_transfer",
            reference_number=None,
            created_at=fixed_time,
        )
        await uow.payments.save(payment1)
        await uow.payments.save(payment2)

        use_case = ListPaymentsUseCase()
        filters = PaymentFilters(invoice_id=invoice_id_1.value)
        pagination = PaginationParams(offset=0, limit=20)
        sort = SortParams(sort_by="created_at", sort_order="desc")

        # Act
        result = await use_case.execute(uow, filters, pagination, sort, fixed_time)

        # Assert
        assert result.total == 1
        assert result.items[0].invoice_id == invoice_id_1
