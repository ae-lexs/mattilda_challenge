"""Tests for schools endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mattilda_challenge.application.common import Page
from mattilda_challenge.application.ports.time_provider import TimeProvider
from mattilda_challenge.application.ports.unit_of_work import UnitOfWork
from mattilda_challenge.domain.entities import School
from mattilda_challenge.domain.value_objects import SchoolId
from mattilda_challenge.entrypoints.http.app import create_app
from mattilda_challenge.entrypoints.http.dependencies import (
    get_db_session,
    get_redis,
    get_school_account_statement_cache,
    get_time_provider,
    get_unit_of_work,
)


@pytest.fixture
def fixed_time() -> datetime:
    """Provide fixed UTC timestamp for testing."""
    return datetime(2024, 1, 15, 12, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_school_id() -> SchoolId:
    """Provide fixed school ID for testing."""
    return SchoolId(value=UUID("11111111-1111-1111-1111-111111111111"))


@pytest.fixture
def sample_school(fixed_school_id: SchoolId, fixed_time: datetime) -> School:
    """Provide sample school entity for testing."""
    return School(
        id=fixed_school_id,
        name="Test School",
        address="123 Test Street",
        created_at=fixed_time,
    )


@pytest.fixture
def mock_time_provider(fixed_time: datetime) -> TimeProvider:
    """Provide mock time provider returning fixed time."""
    provider = MagicMock(spec=TimeProvider)
    provider.now.return_value = fixed_time
    return provider


@pytest.fixture
def mock_uow(sample_school: School) -> UnitOfWork:
    """Provide mock unit of work with mocked repositories."""
    uow = AsyncMock(spec=UnitOfWork)
    uow.schools = AsyncMock()
    uow.students = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def mock_school_cache() -> Any:
    """Provide mock school account statement cache."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


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
    mock_school_cache: Any,
    mock_redis: AsyncMock,
    mock_session: AsyncMock,
) -> FastAPI:
    """Create FastAPI app with mocked dependencies."""
    application = create_app()

    application.dependency_overrides[get_unit_of_work] = lambda: mock_uow
    application.dependency_overrides[get_time_provider] = lambda: mock_time_provider
    application.dependency_overrides[get_school_account_statement_cache] = (
        lambda: mock_school_cache
    )
    application.dependency_overrides[get_redis] = lambda: mock_redis
    application.dependency_overrides[get_db_session] = lambda: mock_session

    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Provide TestClient for endpoint testing."""
    return TestClient(app, raise_server_exceptions=False)


class TestListSchools:
    """Tests for GET /api/v1/schools endpoint."""

    def test_returns_200_ok(self, client: TestClient, mock_uow: UnitOfWork) -> None:
        """Test that list schools returns 200 OK."""
        mock_uow.schools.list = AsyncMock(
            return_value=Page(items=[], total=0, offset=0, limit=20)
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.ListSchoolsUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[], total=0, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/schools")

        assert response.status_code == 200

    def test_returns_paginated_response(
        self, client: TestClient, sample_school: School
    ) -> None:
        """Test that list schools returns paginated response."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.ListSchoolsUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[sample_school], total=1, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/schools")

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data

    def test_returns_school_data(
        self, client: TestClient, sample_school: School
    ) -> None:
        """Test that list schools returns correct school data."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.ListSchoolsUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[sample_school], total=1, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/schools")

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test School"
        assert data["items"][0]["address"] == "123 Test Street"


class TestCreateSchool:
    """Tests for POST /api/v1/schools endpoint."""

    def test_returns_201_created(
        self, client: TestClient, sample_school: School
    ) -> None:
        """Test that create school returns 201 Created."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.CreateSchoolUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_school)
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/schools",
                json={"name": "Test School", "address": "123 Test Street"},
            )

        assert response.status_code == 201

    def test_returns_created_school_data(
        self, client: TestClient, sample_school: School
    ) -> None:
        """Test that create school returns created school data."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.CreateSchoolUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_school)
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/schools",
                json={"name": "Test School", "address": "123 Test Street"},
            )

        data = response.json()
        assert data["name"] == "Test School"
        assert data["address"] == "123 Test Street"
        assert "id" in data
        assert "created_at" in data

    def test_returns_422_for_invalid_input(self, client: TestClient) -> None:
        """Test that create school returns 422 for invalid input."""
        response = client.post(
            "/api/v1/schools",
            json={"name": "", "address": "123 Test Street"},  # Empty name
        )

        assert response.status_code == 422

    def test_returns_422_for_missing_fields(self, client: TestClient) -> None:
        """Test that create school returns 422 for missing fields."""
        response = client.post(
            "/api/v1/schools",
            json={"name": "Test School"},  # Missing address
        )

        assert response.status_code == 422


class TestGetSchool:
    """Tests for GET /api/v1/schools/{school_id} endpoint."""

    def test_returns_200_for_existing_school(
        self,
        client: TestClient,
        mock_uow: UnitOfWork,
        sample_school: School,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test that get school returns 200 for existing school."""
        mock_uow.schools.get_by_id = AsyncMock(return_value=sample_school)

        response = client.get(f"/api/v1/schools/{fixed_school_id.value}")

        assert response.status_code == 200

    def test_returns_school_data(
        self,
        client: TestClient,
        mock_uow: UnitOfWork,
        sample_school: School,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test that get school returns correct school data."""
        mock_uow.schools.get_by_id = AsyncMock(return_value=sample_school)

        response = client.get(f"/api/v1/schools/{fixed_school_id.value}")

        data = response.json()
        assert data["id"] == str(fixed_school_id.value)
        assert data["name"] == "Test School"
        assert data["address"] == "123 Test Street"

    def test_returns_404_for_nonexistent_school(
        self, client: TestClient, mock_uow: UnitOfWork
    ) -> None:
        """Test that get school returns 404 for nonexistent school."""
        mock_uow.schools.get_by_id = AsyncMock(return_value=None)

        response = client.get("/api/v1/schools/99999999-9999-9999-9999-999999999999")

        assert response.status_code == 404


class TestUpdateSchool:
    """Tests for PUT /api/v1/schools/{school_id} endpoint."""

    def test_returns_200_for_successful_update(
        self,
        client: TestClient,
        sample_school: School,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test that update school returns 200 for successful update."""
        updated_school = School(
            id=sample_school.id,
            name="Updated School",
            address=sample_school.address,
            created_at=sample_school.created_at,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.UpdateSchoolUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=updated_school)
            MockUseCase.return_value = mock_instance

            response = client.put(
                f"/api/v1/schools/{fixed_school_id.value}",
                json={"name": "Updated School"},
            )

        assert response.status_code == 200

    def test_returns_updated_school_data(
        self,
        client: TestClient,
        sample_school: School,
        fixed_school_id: SchoolId,
    ) -> None:
        """Test that update school returns updated data."""
        updated_school = School(
            id=sample_school.id,
            name="Updated School",
            address="Updated Address",
            created_at=sample_school.created_at,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.UpdateSchoolUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=updated_school)
            MockUseCase.return_value = mock_instance

            response = client.put(
                f"/api/v1/schools/{fixed_school_id.value}",
                json={"name": "Updated School", "address": "Updated Address"},
            )

        data = response.json()
        assert data["name"] == "Updated School"
        assert data["address"] == "Updated Address"

    def test_returns_404_for_nonexistent_school(self, client: TestClient) -> None:
        """Test that update school returns 404 for nonexistent school."""
        from mattilda_challenge.domain.exceptions import SchoolNotFoundError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.UpdateSchoolUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=SchoolNotFoundError("School not found")
            )
            MockUseCase.return_value = mock_instance

            response = client.put(
                "/api/v1/schools/99999999-9999-9999-9999-999999999999",
                json={"name": "Updated School"},
            )

        assert response.status_code == 404


class TestDeleteSchool:
    """Tests for DELETE /api/v1/schools/{school_id} endpoint."""

    def test_returns_204_for_successful_delete(
        self, client: TestClient, fixed_school_id: SchoolId
    ) -> None:
        """Test that delete school returns 204 for successful delete."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.DeleteSchoolUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=None)
            MockUseCase.return_value = mock_instance

            response = client.delete(f"/api/v1/schools/{fixed_school_id.value}")

        assert response.status_code == 204

    def test_returns_404_for_nonexistent_school(self, client: TestClient) -> None:
        """Test that delete school returns 404 for nonexistent school."""
        from mattilda_challenge.domain.exceptions import SchoolNotFoundError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.DeleteSchoolUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=SchoolNotFoundError("School not found")
            )
            MockUseCase.return_value = mock_instance

            response = client.delete(
                "/api/v1/schools/99999999-9999-9999-9999-999999999999"
            )

        assert response.status_code == 404


class TestGetSchoolAccountStatement:
    """Tests for GET /api/v1/schools/{school_id}/account-statement endpoint."""

    def test_returns_200_for_existing_school(
        self,
        client: TestClient,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
    ) -> None:
        """Test that account statement returns 200 for existing school."""
        from mattilda_challenge.application.dtos import SchoolAccountStatement

        statement = SchoolAccountStatement(
            school_id=fixed_school_id,
            school_name="Test School",
            total_students=15,
            active_students=10,
            total_invoiced=Decimal("10000.00"),
            total_paid=Decimal("7500.00"),
            total_pending=Decimal("2500.00"),
            invoices_pending=3,
            invoices_partially_paid=1,
            invoices_paid=5,
            invoices_overdue=2,
            invoices_cancelled=1,
            total_late_fees=Decimal("125.00"),
            statement_date=fixed_time,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.GetSchoolAccountStatementUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=statement)
            MockUseCase.return_value = mock_instance

            response = client.get(
                f"/api/v1/schools/{fixed_school_id.value}/account-statement"
            )

        assert response.status_code == 200

    def test_returns_financial_summary(
        self,
        client: TestClient,
        fixed_school_id: SchoolId,
        fixed_time: datetime,
    ) -> None:
        """Test that account statement returns financial summary."""
        from mattilda_challenge.application.dtos import SchoolAccountStatement

        statement = SchoolAccountStatement(
            school_id=fixed_school_id,
            school_name="Test School",
            total_students=15,
            active_students=10,
            total_invoiced=Decimal("10000.00"),
            total_paid=Decimal("7500.00"),
            total_pending=Decimal("2500.00"),
            invoices_pending=3,
            invoices_partially_paid=1,
            invoices_paid=5,
            invoices_overdue=2,
            invoices_cancelled=1,
            total_late_fees=Decimal("125.00"),
            statement_date=fixed_time,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.schools.GetSchoolAccountStatementUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=statement)
            MockUseCase.return_value = mock_instance

            response = client.get(
                f"/api/v1/schools/{fixed_school_id.value}/account-statement"
            )

        data = response.json()
        assert data["total_invoiced"] == "10000.00"
        assert data["total_paid"] == "7500.00"
        assert data["total_pending"] == "2500.00"
        assert data["total_late_fees"] == "125.00"
        assert data["active_students"] == 10
