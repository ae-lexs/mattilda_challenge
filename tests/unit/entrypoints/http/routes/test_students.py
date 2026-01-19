"""Tests for students endpoints."""

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
from mattilda_challenge.domain.entities import Student
from mattilda_challenge.domain.value_objects import SchoolId, StudentId, StudentStatus
from mattilda_challenge.entrypoints.http.app import create_app
from mattilda_challenge.entrypoints.http.dependencies import (
    get_db_session,
    get_redis,
    get_student_account_statement_cache,
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
def fixed_student_id() -> StudentId:
    """Provide fixed student ID for testing."""
    return StudentId(value=UUID("22222222-2222-2222-2222-222222222222"))


@pytest.fixture
def sample_student(
    fixed_student_id: StudentId,
    fixed_school_id: SchoolId,
    fixed_time: datetime,
) -> Student:
    """Provide sample student entity for testing."""
    return Student(
        id=fixed_student_id,
        school_id=fixed_school_id,
        first_name="John",
        last_name="Doe",
        email="john.doe@test.com",
        enrollment_date=fixed_time,
        status=StudentStatus.ACTIVE,
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
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    return uow


@pytest.fixture
def mock_student_cache() -> Any:
    """Provide mock student account statement cache."""
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
    mock_student_cache: Any,
    mock_redis: AsyncMock,
    mock_session: AsyncMock,
) -> FastAPI:
    """Create FastAPI app with mocked dependencies."""
    application = create_app()

    application.dependency_overrides[get_unit_of_work] = lambda: mock_uow
    application.dependency_overrides[get_time_provider] = lambda: mock_time_provider
    application.dependency_overrides[get_student_account_statement_cache] = (
        lambda: mock_student_cache
    )
    application.dependency_overrides[get_redis] = lambda: mock_redis
    application.dependency_overrides[get_db_session] = lambda: mock_session

    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Provide TestClient for endpoint testing."""
    return TestClient(app, raise_server_exceptions=False)


class TestListStudents:
    """Tests for GET /api/v1/students endpoint."""

    def test_returns_200_ok(self, client: TestClient) -> None:
        """Test that list students returns 200 OK."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.ListStudentsUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[], total=0, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/students")

        assert response.status_code == 200

    def test_returns_paginated_response(
        self, client: TestClient, sample_student: Student
    ) -> None:
        """Test that list students returns paginated response."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.ListStudentsUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[sample_student], total=1, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get("/api/v1/students")

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data

    def test_filters_by_school_id(
        self, client: TestClient, sample_student: Student, fixed_school_id: SchoolId
    ) -> None:
        """Test that list students can filter by school_id."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.ListStudentsUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                return_value=Page(items=[sample_student], total=1, offset=0, limit=20)
            )
            MockUseCase.return_value = mock_instance

            response = client.get(f"/api/v1/students?school_id={fixed_school_id.value}")

        assert response.status_code == 200


class TestCreateStudent:
    """Tests for POST /api/v1/students endpoint."""

    def test_returns_201_created(
        self, client: TestClient, sample_student: Student, fixed_school_id: SchoolId
    ) -> None:
        """Test that create student returns 201 Created."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.CreateStudentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_student)
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/students",
                json={
                    "school_id": str(fixed_school_id.value),
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@test.com",
                },
            )

        assert response.status_code == 201

    def test_returns_created_student_data(
        self, client: TestClient, sample_student: Student, fixed_school_id: SchoolId
    ) -> None:
        """Test that create student returns created student data."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.CreateStudentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=sample_student)
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/students",
                json={
                    "school_id": str(fixed_school_id.value),
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@test.com",
                },
            )

        data = response.json()
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["email"] == "john.doe@test.com"
        assert "id" in data

    def test_returns_422_for_invalid_email(self, client: TestClient) -> None:
        """Test that create student returns 422 for invalid email."""
        response = client.post(
            "/api/v1/students",
            json={
                "school_id": "11111111-1111-1111-1111-111111111111",
                "first_name": "John",
                "last_name": "Doe",
                "email": "invalid-email",
            },
        )

        assert response.status_code == 422

    def test_returns_404_for_nonexistent_school(self, client: TestClient) -> None:
        """Test that create student returns 404 for nonexistent school."""
        from mattilda_challenge.domain.exceptions import SchoolNotFoundError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.CreateStudentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=SchoolNotFoundError("School not found")
            )
            MockUseCase.return_value = mock_instance

            response = client.post(
                "/api/v1/students",
                json={
                    "school_id": "99999999-9999-9999-9999-999999999999",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@test.com",
                },
            )

        assert response.status_code == 404


class TestGetStudent:
    """Tests for GET /api/v1/students/{student_id} endpoint."""

    def test_returns_200_for_existing_student(
        self,
        client: TestClient,
        mock_uow: UnitOfWork,
        sample_student: Student,
        fixed_student_id: StudentId,
    ) -> None:
        """Test that get student returns 200 for existing student."""
        mock_uow.students.get_by_id = AsyncMock(return_value=sample_student)

        response = client.get(f"/api/v1/students/{fixed_student_id.value}")

        assert response.status_code == 200

    def test_returns_student_data(
        self,
        client: TestClient,
        mock_uow: UnitOfWork,
        sample_student: Student,
        fixed_student_id: StudentId,
    ) -> None:
        """Test that get student returns correct student data."""
        mock_uow.students.get_by_id = AsyncMock(return_value=sample_student)

        response = client.get(f"/api/v1/students/{fixed_student_id.value}")

        data = response.json()
        assert data["id"] == str(fixed_student_id.value)
        assert data["first_name"] == "John"
        assert data["last_name"] == "Doe"
        assert data["status"] == "active"

    def test_returns_404_for_nonexistent_student(
        self, client: TestClient, mock_uow: UnitOfWork
    ) -> None:
        """Test that get student returns 404 for nonexistent student."""
        mock_uow.students.get_by_id = AsyncMock(return_value=None)

        response = client.get("/api/v1/students/99999999-9999-9999-9999-999999999999")

        assert response.status_code == 404


class TestUpdateStudent:
    """Tests for PUT /api/v1/students/{student_id} endpoint."""

    def test_returns_200_for_successful_update(
        self, client: TestClient, sample_student: Student, fixed_student_id: StudentId
    ) -> None:
        """Test that update student returns 200 for successful update."""
        updated_student = Student(
            id=sample_student.id,
            school_id=sample_student.school_id,
            first_name="Jane",
            last_name=sample_student.last_name,
            email=sample_student.email,
            enrollment_date=sample_student.enrollment_date,
            status=sample_student.status,
            created_at=sample_student.created_at,
            updated_at=sample_student.updated_at,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.UpdateStudentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=updated_student)
            MockUseCase.return_value = mock_instance

            response = client.put(
                f"/api/v1/students/{fixed_student_id.value}",
                json={"first_name": "Jane"},
            )

        assert response.status_code == 200

    def test_returns_404_for_nonexistent_student(self, client: TestClient) -> None:
        """Test that update student returns 404 for nonexistent student."""
        from mattilda_challenge.domain.exceptions import StudentNotFoundError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.UpdateStudentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=StudentNotFoundError("Student not found")
            )
            MockUseCase.return_value = mock_instance

            response = client.put(
                "/api/v1/students/99999999-9999-9999-9999-999999999999",
                json={"first_name": "Jane"},
            )

        assert response.status_code == 404


class TestDeleteStudent:
    """Tests for DELETE /api/v1/students/{student_id} endpoint."""

    def test_returns_204_for_successful_delete(
        self, client: TestClient, fixed_student_id: StudentId
    ) -> None:
        """Test that delete student returns 204 for successful delete."""
        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.DeleteStudentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=None)
            MockUseCase.return_value = mock_instance

            response = client.delete(f"/api/v1/students/{fixed_student_id.value}")

        assert response.status_code == 204

    def test_returns_404_for_nonexistent_student(self, client: TestClient) -> None:
        """Test that delete student returns 404 for nonexistent student."""
        from mattilda_challenge.domain.exceptions import StudentNotFoundError

        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.DeleteStudentUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(
                side_effect=StudentNotFoundError("Student not found")
            )
            MockUseCase.return_value = mock_instance

            response = client.delete(
                "/api/v1/students/99999999-9999-9999-9999-999999999999"
            )

        assert response.status_code == 404


class TestGetStudentAccountStatement:
    """Tests for GET /api/v1/students/{student_id}/account-statement endpoint."""

    def test_returns_200_for_existing_student(
        self, client: TestClient, fixed_student_id: StudentId, fixed_time: datetime
    ) -> None:
        """Test that account statement returns 200 for existing student."""
        from mattilda_challenge.application.dtos import StudentAccountStatement

        statement = StudentAccountStatement(
            student_id=fixed_student_id,
            student_name="John Doe",
            school_name="Test School",
            total_invoiced=Decimal("5000.00"),
            total_paid=Decimal("3000.00"),
            total_pending=Decimal("2000.00"),
            invoices_pending=2,
            invoices_partially_paid=1,
            invoices_paid=3,
            invoices_cancelled=0,
            invoices_overdue=1,
            total_late_fees=Decimal("50.00"),
            statement_date=fixed_time,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.GetStudentAccountStatementUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=statement)
            MockUseCase.return_value = mock_instance

            response = client.get(
                f"/api/v1/students/{fixed_student_id.value}/account-statement"
            )

        assert response.status_code == 200

    def test_returns_financial_summary(
        self, client: TestClient, fixed_student_id: StudentId, fixed_time: datetime
    ) -> None:
        """Test that account statement returns financial summary."""
        from mattilda_challenge.application.dtos import StudentAccountStatement

        statement = StudentAccountStatement(
            student_id=fixed_student_id,
            student_name="John Doe",
            school_name="Test School",
            total_invoiced=Decimal("5000.00"),
            total_paid=Decimal("3000.00"),
            total_pending=Decimal("2000.00"),
            invoices_pending=2,
            invoices_partially_paid=1,
            invoices_paid=3,
            invoices_cancelled=0,
            invoices_overdue=1,
            total_late_fees=Decimal("50.00"),
            statement_date=fixed_time,
        )

        with patch(
            "mattilda_challenge.entrypoints.http.routes.students.GetStudentAccountStatementUseCase"
        ) as MockUseCase:
            mock_instance = AsyncMock()
            mock_instance.execute = AsyncMock(return_value=statement)
            MockUseCase.return_value = mock_instance

            response = client.get(
                f"/api/v1/students/{fixed_student_id.value}/account-statement"
            )

        data = response.json()
        assert data["total_invoiced"] == "5000.00"
        assert data["total_paid"] == "3000.00"
        assert data["total_pending"] == "2000.00"
        assert data["invoices_overdue"] == 1
        assert data["total_late_fees"] == "50.00"
