"""Tests for health check endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mattilda_challenge.entrypoints.http.app import create_app
from mattilda_challenge.entrypoints.http.dependencies import (
    get_db_session,
    get_redis,
)


@pytest.fixture
def mock_session() -> AsyncMock:
    """Provide mock database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_redis_healthy() -> AsyncMock:
    """Provide mock Redis client that returns healthy."""
    redis = AsyncMock()
    redis.ping = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_redis_unhealthy() -> AsyncMock:
    """Provide mock Redis client that raises error."""
    redis = AsyncMock()
    redis.ping = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
    return redis


@pytest.fixture
def app_healthy(mock_session: AsyncMock, mock_redis_healthy: AsyncMock) -> FastAPI:
    """Create app with healthy dependencies."""
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: mock_session
    application.dependency_overrides[get_redis] = lambda: mock_redis_healthy
    return application


@pytest.fixture
def app_unhealthy_redis(
    mock_session: AsyncMock, mock_redis_unhealthy: AsyncMock
) -> FastAPI:
    """Create app with unhealthy Redis."""
    application = create_app()
    application.dependency_overrides[get_db_session] = lambda: mock_session
    application.dependency_overrides[get_redis] = lambda: mock_redis_unhealthy
    return application


@pytest.fixture
def client_healthy(app_healthy: FastAPI) -> TestClient:
    """Provide TestClient with healthy dependencies."""
    return TestClient(app_healthy, raise_server_exceptions=False)


@pytest.fixture
def client_unhealthy(app_unhealthy_redis: FastAPI) -> TestClient:
    """Provide TestClient with unhealthy Redis."""
    return TestClient(app_unhealthy_redis, raise_server_exceptions=False)


class TestLivenessEndpoint:
    """Tests for /health/live endpoint."""

    def test_returns_200_ok(self, client_healthy: TestClient) -> None:
        """Test that liveness endpoint returns 200 OK."""
        response = client_healthy.get("/health/live")
        assert response.status_code == 200

    def test_returns_alive_status(self, client_healthy: TestClient) -> None:
        """Test that liveness endpoint returns alive status."""
        response = client_healthy.get("/health/live")
        data = response.json()
        assert data["status"] == "alive"

    def test_does_not_check_dependencies(self, app_unhealthy_redis: FastAPI) -> None:
        """Test that liveness does not check external dependencies."""
        # Even with unhealthy Redis, liveness should return 200
        client = TestClient(app_unhealthy_redis, raise_server_exceptions=False)
        response = client.get("/health/live")
        assert response.status_code == 200


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_returns_200_when_all_healthy(self, client_healthy: TestClient) -> None:
        """Test that health endpoint returns 200 when all dependencies healthy."""
        response = client_healthy.get("/health")
        assert response.status_code == 200

    def test_returns_healthy_status_when_all_healthy(
        self, client_healthy: TestClient
    ) -> None:
        """Test that health endpoint returns healthy status."""
        response = client_healthy.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_includes_dependencies_in_response(
        self, client_healthy: TestClient
    ) -> None:
        """Test that health endpoint includes dependency statuses."""
        response = client_healthy.get("/health")
        data = response.json()
        assert "dependencies" in data
        assert "database" in data["dependencies"]
        assert "redis" in data["dependencies"]

    def test_includes_version_in_response(self, client_healthy: TestClient) -> None:
        """Test that health endpoint includes app version."""
        response = client_healthy.get("/health")
        data = response.json()
        assert "version" in data

    def test_includes_timestamp_in_response(self, client_healthy: TestClient) -> None:
        """Test that health endpoint includes timestamp."""
        response = client_healthy.get("/health")
        data = response.json()
        assert "timestamp" in data

    def test_returns_503_when_redis_unhealthy(
        self, client_unhealthy: TestClient
    ) -> None:
        """Test that health endpoint returns 503 when Redis is unhealthy."""
        response = client_unhealthy.get("/health")
        assert response.status_code == 503

    def test_returns_unhealthy_status_when_redis_unhealthy(
        self, client_unhealthy: TestClient
    ) -> None:
        """Test that health endpoint returns unhealthy status."""
        response = client_unhealthy.get("/health")
        data = response.json()
        assert data["status"] == "unhealthy"


class TestReadinessEndpoint:
    """Tests for /health/ready endpoint."""

    def test_returns_200_when_all_healthy(self, client_healthy: TestClient) -> None:
        """Test that readiness endpoint returns 200 when all healthy."""
        response = client_healthy.get("/health/ready")
        assert response.status_code == 200

    def test_returns_healthy_status(self, client_healthy: TestClient) -> None:
        """Test that readiness endpoint returns healthy status."""
        response = client_healthy.get("/health/ready")
        data = response.json()
        assert data["status"] == "healthy"

    def test_returns_503_when_dependency_unhealthy(
        self, client_unhealthy: TestClient
    ) -> None:
        """Test that readiness returns 503 when dependency unhealthy."""
        response = client_unhealthy.get("/health/ready")
        assert response.status_code == 503

    def test_includes_dependency_statuses(self, client_healthy: TestClient) -> None:
        """Test that readiness includes dependency statuses."""
        response = client_healthy.get("/health/ready")
        data = response.json()
        assert "dependencies" in data
        assert data["dependencies"]["database"]["status"] == "healthy"
        assert data["dependencies"]["redis"]["status"] == "healthy"
