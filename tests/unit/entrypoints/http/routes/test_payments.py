"""Tests for payments endpoints."""

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
from mattilda_challenge.domain.entities import Payment
from mattilda_challenge.domain.value_objects import InvoiceId, PaymentId
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
def fixed_invoice_id() -> InvoiceId:
    """Provide fixed invoice ID for testing."""
    return InvoiceId(value=UUID("33333333-3333-3333-3333-333333333333"))


@pytest.fixture
def fixed_payment_id() -> PaymentId:
    """Provide fixed payment ID for testing."""
    return PaymentId(value=UUID("44444444-4444-4444-4444-444444444444"))


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
        payment_method="transfer",
        reference_number="REF-001",
        created_at=fixed_time,
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


class TestListPayments:
    """Tests for GET /api/v1/payments endpoint."""

    def test_returns_200_ok(self, client: TestClient) -> None:
        """Test that list payments returns 200 OK."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.payments.ListPaymentsUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[], total=0, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/payments")

        assert response.status_code == 200

    def test_returns_paginated_response(
        self, client: TestClient, sample_payment: Payment
    ) -> None:
        """Test that list payments returns paginated response."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.payments.ListPaymentsUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[sample_payment], total=1, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/payments")

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data

    def test_filters_by_invoice_id(
        self, client: TestClient, sample_payment: Payment, fixed_invoice_id: InvoiceId
    ) -> None:
        """Test that list payments can filter by invoice_id."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.payments.ListPaymentsUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[sample_payment], total=1, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get(
                f"/api/v1/payments?invoice_id={fixed_invoice_id.value}"
            )

        assert response.status_code == 200


class TestRecordPayment:
    """Tests for POST /api/v1/payments endpoint."""

    def test_returns_201_created(
        self, client: TestClient, sample_payment: Payment, fixed_invoice_id: InvoiceId
    ) -> None:
        """Test that record payment returns 201 Created."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.payments.RecordPaymentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_payment)
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/payments",
                json={
                    "invoice_id": str(fixed_invoice_id.value),
                    "amount": "500.00",
                    "payment_date": "2024-01-15T10:30:00Z",
                    "payment_method": "transfer",
                    "reference_number": "REF-001",
                },
            )

        assert response.status_code == 201

    def test_returns_created_payment_data(
        self, client: TestClient, sample_payment: Payment, fixed_invoice_id: InvoiceId
    ) -> None:
        """Test that record payment returns created payment data."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.payments.RecordPaymentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_payment)
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/payments",
                json={
                    "invoice_id": str(fixed_invoice_id.value),
                    "amount": "500.00",
                    "payment_date": "2024-01-15T10:30:00Z",
                    "payment_method": "transfer",
                    "reference_number": "REF-001",
                },
            )

        data = response.json()
        assert data["amount"] == "500.00"
        assert data["payment_method"] == "transfer"
        assert data["reference_number"] == "REF-001"
        assert "id" in data

    def test_returns_201_without_reference_number(
        self, client: TestClient, fixed_invoice_id: InvoiceId, fixed_time: datetime
    ) -> None:
        """Test that record payment works without reference number."""
        payment_without_ref = Payment(
            id=PaymentId.generate(),
            invoice_id=fixed_invoice_id,
            amount=Decimal("500.00"),
            payment_date=fixed_time,
            payment_method="cash",
            reference_number=None,
            created_at=fixed_time,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.payments.RecordPaymentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=payment_without_ref)
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/payments",
                json={
                    "invoice_id": str(fixed_invoice_id.value),
                    "amount": "500.00",
                    "payment_date": "2024-01-15T10:30:00Z",
                    "payment_method": "cash",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["reference_number"] is None

    def test_returns_422_for_invalid_amount_format(self, client: TestClient) -> None:
        """Test that record payment returns 422 for invalid amount format."""
        response = client.post(
            "/api/v1/payments",
            json={
                "invoice_id": "33333333-3333-3333-3333-333333333333",
                "amount": "500",  # Missing decimal places
                "payment_date": "2024-01-15T10:30:00Z",
                "payment_method": "transfer",
            },
        )

        assert response.status_code == 422

    def test_returns_404_for_nonexistent_invoice(self, client: TestClient) -> None:
        """Test that record payment returns 404 for nonexistent invoice."""
        from mattilda_challenge.domain.exceptions import InvoiceNotFoundError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.payments.RecordPaymentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=InvoiceNotFoundError("Invoice not found")
            )
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/payments",
                json={
                    "invoice_id": "99999999-9999-9999-9999-999999999999",
                    "amount": "500.00",
                    "payment_date": "2024-01-15T10:30:00Z",
                    "payment_method": "transfer",
                },
            )

        assert response.status_code == 404

    def test_returns_400_for_invalid_payment_amount(self, client: TestClient) -> None:
        """Test that record payment returns 400 for invalid payment amount."""
        from mattilda_challenge.domain.exceptions import PaymentExceedsBalanceError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.payments.RecordPaymentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=PaymentExceedsBalanceError(
                    "Payment exceeds remaining balance"
                )
            )
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/payments",
                json={
                    "invoice_id": "33333333-3333-3333-3333-333333333333",
                    "amount": "99999.00",  # Exceeds invoice amount
                    "payment_date": "2024-01-15T10:30:00Z",
                    "payment_method": "transfer",
                },
            )

        assert response.status_code == 400

    def test_returns_400_for_cancelled_invoice(self, client: TestClient) -> None:
        """Test that record payment returns 400 for cancelled invoice."""
        from mattilda_challenge.domain.exceptions import CannotPayCancelledInvoiceError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.payments.RecordPaymentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=CannotPayCancelledInvoiceError(
                    "Cannot pay cancelled invoice"
                )
            )
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/payments",
                json={
                    "invoice_id": "33333333-3333-3333-3333-333333333333",
                    "amount": "500.00",
                    "payment_date": "2024-01-15T10:30:00Z",
                    "payment_method": "transfer",
                },
            )

        assert response.status_code == 400


class TestGetPayment:
    """Tests for GET /api/v1/payments/{payment_id} endpoint."""

    def test_returns_200_for_existing_payment(
        self,
        client: TestClient,
        mock_uow: UnitOfWork,
        sample_payment: Payment,
        fixed_payment_id: PaymentId,
    ) -> None:
        """Test that get payment returns 200 for existing payment."""
        mock_uow.payments.get_by_id = AsyncMock(return_value=sample_payment)

        response = client.get(f"/api/v1/payments/{fixed_payment_id.value}")

        assert response.status_code == 200

    def test_returns_payment_data(
        self,
        client: TestClient,
        mock_uow: UnitOfWork,
        sample_payment: Payment,
        fixed_payment_id: PaymentId,
    ) -> None:
        """Test that get payment returns correct payment data."""
        mock_uow.payments.get_by_id = AsyncMock(return_value=sample_payment)

        response = client.get(f"/api/v1/payments/{fixed_payment_id.value}")

        data = response.json()
        assert data["id"] == str(fixed_payment_id.value)
        assert data["amount"] == "500.00"
        assert data["payment_method"] == "transfer"
        assert data["reference_number"] == "REF-001"

    def test_returns_404_for_nonexistent_payment(
        self, client: TestClient, mock_uow: UnitOfWork
    ) -> None:
        """Test that get payment returns 404 for nonexistent payment."""
        mock_uow.payments.get_by_id = AsyncMock(return_value=None)

        response = client.get("/api/v1/payments/99999999-9999-9999-9999-999999999999")

        assert response.status_code == 404
