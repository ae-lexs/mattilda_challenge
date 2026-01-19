"""Tests for invoices endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mattilda_challenge.application.common import Page
from mattilda_challenge.application.ports.time_provider import TimeProvider
from mattilda_challenge.application.ports.unit_of_work import UnitOfWork
from mattilda_challenge.domain.entities import Invoice
from mattilda_challenge.domain.value_objects import (
    InvoiceId,
    InvoiceStatus,
    LateFeePolicy,
    StudentId,
)
from mattilda_challenge.entrypoints.http.app import create_app
from mattilda_challenge.entrypoints.http.dependencies import (
    get_db_session,
    get_redis,
    get_time_provider,
    get_unit_of_work,
)


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def fixed_invoice_id() -> InvoiceId:
    """Provide fixed invoice ID for testing."""
    return InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333"))


@pytest.fixture
def standard_late_fee_policy() -> LateFeePolicy:
    """Provide standard late fee policy for testing."""
    return LateFeePolicy(monthly_rate=Decimal("0.05"))


@pytest.fixture
def sample_invoice(
    fixed_invoice_id: InvoiceId,
    fixed_student_id: StudentId,
    fixed_time: datetime,
    standard_late_fee_policy: LateFeePolicy,
) -> Invoice:
    """Provide sample invoice entity for testing."""
    due_date = datetime(2024, 2, 15, 0, 0, 0, tzinfo=UTC)
    return Invoice(
        id=fixed_invoice_id,
        student_id=fixed_student_id,
        invoice_number="INV-2024-000001",
        amount=Decimal("1500.00"),
        due_date=due_date,
        description="January 2024 Tuition",
        late_fee_policy=standard_late_fee_policy,
        status=InvoiceStatus.PENDING,
        created_at=fixed_time,
        updated_at=fixed_time,
    )


@pytest.fixture
def mock_time_provider(fixed_time: datetime) -> TimeProvider:
    """Provide mock time provider returning fixed time."""
    provider = MagicMock(spec=TimeProvider)
    provider.now.return_value = fixed_time
    return provider


@pytest.fixture
def mock_uow() -> UnitOfWork:
    """Provide mock unit of work with mocked repositories."""
    uow = AsyncMock(spec=UnitOfWork)
    uow.schools = AsyncMock()
    uow.students = AsyncMock()
    uow.invoices = AsyncMock()
    uow.payments = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Provide mock Redis client."""
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_session() -> AsyncMock:
    """Provide mock database session."""
    return AsyncMock()


@pytest.fixture
def app(
    mock_uow: UnitOfWork,
    mock_time_provider: TimeProvider,
    mock_redis: AsyncMock,
    mock_session: AsyncMock,
) -> FastAPI:
    """Create FastAPI app with mocked dependencies."""
    application = create_app()

    application.dependency_overrides[get_unit_of_work] = lambda: mock_uow
    application.dependency_overrides[get_time_provider] = lambda: mock_time_provider
    application.dependency_overrides[get_redis] = lambda: mock_redis
    application.dependency_overrides[get_db_session] = lambda: mock_session

    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Provide TestClient for endpoint testing."""
    return TestClient(app, raise_server_exceptions=False)


class TestListInvoices:
    """Tests for GET /api/v1/invoices endpoint."""

    def test_returns_200_ok(self, client: TestClient) -> None:
        """Test that list invoices returns 200 OK."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.ListInvoicesUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[], total=0, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/invoices")

        assert response.status_code == 200

    def test_returns_paginated_response(
        self, client: TestClient, sample_invoice: Invoice
    ) -> None:
        """Test that list invoices returns paginated response."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.ListInvoicesUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[sample_invoice], total=1, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/invoices")

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data

    def test_filters_by_student_id(
        self, client: TestClient, sample_invoice: Invoice, fixed_student_id: StudentId
    ) -> None:
        """Test that list invoices can filter by student_id."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.ListInvoicesUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[sample_invoice], total=1, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get(
                f"/api/v1/invoices?student_id={fixed_student_id.value}"
            )

        assert response.status_code == 200

    def test_filters_by_status(
        self, client: TestClient, sample_invoice: Invoice
    ) -> None:
        """Test that list invoices can filter by status."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.ListInvoicesUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[sample_invoice], total=1, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/invoices?status=pending")

        assert response.status_code == 200


class TestCreateInvoice:
    """Tests for POST /api/v1/invoices endpoint."""

    def test_returns_201_created(
        self, client: TestClient, sample_invoice: Invoice, fixed_student_id: StudentId
    ) -> None:
        """Test that create invoice returns 201 Created."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.CreateInvoiceUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_invoice)
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/invoices",
                json={
                    "student_id": str(fixed_student_id.value),
                    "amount": "1500.00",
                    "due_date": "2024-02-15T00:00:00Z",
                    "description": "January 2024 Tuition",
                    "late_fee_policy_monthly_rate": "0.05",
                },
            )

        assert response.status_code == 201

    def test_returns_created_invoice_data(
        self, client: TestClient, sample_invoice: Invoice, fixed_student_id: StudentId
    ) -> None:
        """Test that create invoice returns created invoice data."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.CreateInvoiceUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_invoice)
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/invoices",
                json={
                    "student_id": str(fixed_student_id.value),
                    "amount": "1500.00",
                    "due_date": "2024-02-15T00:00:00Z",
                    "description": "January 2024 Tuition",
                    "late_fee_policy_monthly_rate": "0.05",
                },
            )

        data = response.json()
        assert data["amount"] == "1500.00"
        assert data["description"] == "January 2024 Tuition"
        assert data["status"] == "pending"
        assert "id" in data
        assert "invoice_number" in data

    def test_returns_422_for_invalid_amount_format(self, client: TestClient) -> None:
        """Test that create invoice returns 422 for invalid amount format."""
        response = client.post(
            "/api/v1/invoices",
            json={
                "student_id": "22222222-2222-2222-2222-222222222222",
                "amount": "1500",  # Missing decimal places
                "due_date": "2024-02-15T00:00:00Z",
                "description": "January 2024 Tuition",
                "late_fee_policy_monthly_rate": "0.05",
            },
        )

        assert response.status_code == 422

    def test_returns_404_for_nonexistent_student(self, client: TestClient) -> None:
        """Test that create invoice returns 404 for nonexistent student."""
        from mattilda_challenge.domain.exceptions import StudentNotFoundError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.CreateInvoiceUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=StudentNotFoundError("Student not found")
            )
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/invoices",
                json={
                    "student_id": "99999999-9999-9999-9999-999999999999",
                    "amount": "1500.00",
                    "due_date": "2024-02-15T00:00:00Z",
                    "description": "January 2024 Tuition",
                    "late_fee_policy_monthly_rate": "0.05",
                },
            )

        assert response.status_code == 404


class TestGetInvoice:
    """Tests for GET /api/v1/invoices/{invoice_id} endpoint."""

    def test_returns_200_for_existing_invoice(
        self,
        client: TestClient,
        mock_uow: UnitOfWork,
        sample_invoice: Invoice,
        fixed_invoice_id: InvoiceId,
    ) -> None:
        """Test that get invoice returns 200 for existing invoice."""
        mock_uow.invoices.get_by_id = AsyncMock(return_value=sample_invoice)

        response = client.get(f"/api/v1/invoices/{fixed_invoice_id.value}")

        assert response.status_code == 200

    def test_returns_invoice_data(
        self,
        client: TestClient,
        mock_uow: UnitOfWork,
        sample_invoice: Invoice,
        fixed_invoice_id: InvoiceId,
    ) -> None:
        """Test that get invoice returns correct invoice data."""
        mock_uow.invoices.get_by_id = AsyncMock(return_value=sample_invoice)

        response = client.get(f"/api/v1/invoices/{fixed_invoice_id.value}")

        data = response.json()
        assert data["id"] == str(fixed_invoice_id.value)
        assert data["amount"] == "1500.00"
        assert data["description"] == "January 2024 Tuition"
        assert data["status"] == "pending"

    def test_returns_computed_fields(
        self,
        client: TestClient,
        mock_uow: UnitOfWork,
        sample_invoice: Invoice,
        fixed_invoice_id: InvoiceId,
    ) -> None:
        """Test that get invoice returns computed fields."""
        mock_uow.invoices.get_by_id = AsyncMock(return_value=sample_invoice)

        response = client.get(f"/api/v1/invoices/{fixed_invoice_id.value}")

        data = response.json()
        assert "is_overdue" in data
        assert "late_fee" in data

    def test_returns_404_for_nonexistent_invoice(
        self, client: TestClient, mock_uow: UnitOfWork
    ) -> None:
        """Test that get invoice returns 404 for nonexistent invoice."""
        mock_uow.invoices.get_by_id = AsyncMock(return_value=None)

        response = client.get("/api/v1/invoices/99999999-9999-9999-9999-999999999999")

        assert response.status_code == 404


class TestCancelInvoice:
    """Tests for POST /api/v1/invoices/{invoice_id}/cancel endpoint."""

    def test_returns_200_for_successful_cancel(
        self, client: TestClient, sample_invoice: Invoice, fixed_invoice_id: InvoiceId
    ) -> None:
        """Test that cancel invoice returns 200 for successful cancel."""
        cancelled_invoice = Invoice(
            id=sample_invoice.id,
            student_id=sample_invoice.student_id,
            invoice_number=sample_invoice.invoice_number,
            amount=sample_invoice.amount,
            due_date=sample_invoice.due_date,
            description=sample_invoice.description,
            late_fee_policy=sample_invoice.late_fee_policy,
            status=InvoiceStatus.CANCELLED,
            created_at=sample_invoice.created_at,
            updated_at=sample_invoice.updated_at,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.CancelInvoiceUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=cancelled_invoice)
            MockUseCase.return_value = mock_instance

            response = client.post(
                f"/api/v1/invoices/{fixed_invoice_id.value}/cancel",
                json={"cancellation_reason": "Student withdrew"},
            )

        assert response.status_code == 200

    def test_returns_cancelled_status(
        self, client: TestClient, sample_invoice: Invoice, fixed_invoice_id: InvoiceId
    ) -> None:
        """Test that cancel invoice returns cancelled status."""
        cancelled_invoice = Invoice(
            id=sample_invoice.id,
            student_id=sample_invoice.student_id,
            invoice_number=sample_invoice.invoice_number,
            amount=sample_invoice.amount,
            due_date=sample_invoice.due_date,
            description=sample_invoice.description,
            late_fee_policy=sample_invoice.late_fee_policy,
            status=InvoiceStatus.CANCELLED,
            created_at=sample_invoice.created_at,
            updated_at=sample_invoice.updated_at,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.CancelInvoiceUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=cancelled_invoice)
            MockUseCase.return_value = mock_instance

            response = client.post(
                f"/api/v1/invoices/{fixed_invoice_id.value}/cancel",
                json={"cancellation_reason": "Student withdrew"},
            )

        data = response.json()
        assert data["status"] == "cancelled"

    def test_returns_404_for_nonexistent_invoice(self, client: TestClient) -> None:
        """Test that cancel invoice returns 404 for nonexistent invoice."""
        from mattilda_challenge.domain.exceptions import InvoiceNotFoundError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.CancelInvoiceUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=InvoiceNotFoundError("Invoice not found")
            )
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/invoices/99999999-9999-9999-9999-999999999999/cancel",
                json={"cancellation_reason": "Student withdrew"},
            )

        assert response.status_code == 404

    def test_returns_400_for_already_cancelled_invoice(
        self, client: TestClient
    ) -> None:
        """Test that cancel invoice returns 400 for already cancelled invoice."""
        from mattilda_challenge.domain.exceptions import InvalidStateTransitionError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.invoices.CancelInvoiceUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=InvalidStateTransitionError("Invoice already cancelled")
            )
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/invoices/33333333-3333-3333-3333-333333333333/cancel",
                json={"cancellation_reason": "Student withdrew"},
            )

        assert response.status_code == 400

    def test_returns_422_for_empty_cancellation_reason(
        self, client: TestClient
    ) -> None:
        """Test that cancel invoice returns 422 for empty cancellation reason."""
        response = client.post(
            "/api/v1/invoices/33333333-3333-3333-3333-333333333333/cancel",
            json={"cancellation_reason": ""},
        )

        assert response.status_code == 422
