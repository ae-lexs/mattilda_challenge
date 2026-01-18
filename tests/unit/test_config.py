"""Tests for application configuration."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from pydantic import ValidationError

import mattilda_challenge.config as config_module
from mattilda_challenge.config import Settings, get_settings


class TestDatabaseUrlSync:
    """Tests for database_url_sync property."""

    def test_converts_asyncpg_to_sync_driver(self) -> None:
        """Test that postgresql+asyncpg:// is converted to postgresql://."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
        )

        result = settings.database_url_sync

        assert result == "postgresql://user:pass@localhost:5432/testdb"

    def test_preserves_connection_string_details(self) -> None:
        """Test that all connection details are preserved after conversion."""
        settings = Settings(
            database_url="postgresql+asyncpg://myuser:secret@db.example.com:5433/mydb",
        )

        result = settings.database_url_sync

        assert "myuser:secret" in result
        assert "db.example.com:5433" in result
        assert "/mydb" in result

    def test_handles_url_without_asyncpg(self) -> None:
        """Test that URLs without asyncpg are unchanged."""
        settings = Settings(
            database_url="postgresql://user:pass@localhost:5432/testdb",
        )

        result = settings.database_url_sync

        assert result == "postgresql://user:pass@localhost:5432/testdb"


class TestSettingsDefaults:
    """Tests for Settings default values.

    These tests use monkeypatch to clear environment variables,
    ensuring we test actual defaults.
    """

    @pytest.fixture(autouse=True)
    def clear_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Clear settings-related environment variables before each test."""
        monkeypatch.delenv("DATABASE_POOL_SIZE", raising=False)
        monkeypatch.delenv("DATABASE_MAX_OVERFLOW", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.delenv("CACHE_TTL_SECONDS", raising=False)
        monkeypatch.delenv("DEBUG", raising=False)

    def test_database_pool_size_default(self) -> None:
        """Test that database_pool_size defaults to 10."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
        )

        assert settings.database_pool_size == 10

    def test_database_max_overflow_default(self) -> None:
        """Test that database_max_overflow defaults to 20."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
        )

        assert settings.database_max_overflow == 20

    def test_redis_url_default(self) -> None:
        """Test that redis_url defaults to localhost."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
        )

        assert settings.redis_url == "redis://localhost:6379/0"

    def test_cache_ttl_seconds_default(self) -> None:
        """Test that cache_ttl_seconds defaults to 300."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
        )

        assert settings.cache_ttl_seconds == 300

    def test_debug_default(self) -> None:
        """Test that debug defaults to False."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
        )

        assert settings.debug is False


class TestSettingsOverrides:
    """Tests for Settings value overrides."""

    def test_can_override_database_pool_size(self) -> None:
        """Test that database_pool_size can be overridden."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
            database_pool_size=25,
        )

        assert settings.database_pool_size == 25

    def test_can_override_debug(self) -> None:
        """Test that debug can be overridden."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
            debug=True,
        )

        assert settings.debug is True

    def test_can_override_redis_url(self) -> None:
        """Test that redis_url can be overridden."""
        settings = Settings(
            database_url="postgresql+asyncpg://user:pass@localhost:5432/testdb",
            redis_url="redis://redis.example.com:6380/1",
        )

        assert settings.redis_url == "redis://redis.example.com:6380/1"


class TestGetSettings:
    """Tests for get_settings() lazy singleton function."""

    @pytest.fixture(autouse=True)
    def reset_settings_singleton(self) -> Generator[None]:
        """Reset the settings singleton before and after each test."""
        config_module._settings = None
        yield
        config_module._settings = None

    def test_returns_settings_instance(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that get_settings() returns a Settings instance."""
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:pass@localhost:5432/testdb",
        )

        result = get_settings()

        assert isinstance(result, Settings)

    def test_returns_same_instance_on_subsequent_calls(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that get_settings() returns the same instance (singleton)."""
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:pass@localhost:5432/testdb",
        )

        first_call = get_settings()
        second_call = get_settings()

        assert first_call is second_call

    def test_reads_database_url_from_environment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that get_settings() reads DATABASE_URL from environment."""
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://envuser:envpass@envhost:5432/envdb",
        )

        result = get_settings()

        assert (
            result.database_url
            == "postgresql+asyncpg://envuser:envpass@envhost:5432/envdb"
        )

    def test_reads_other_settings_from_environment(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test that get_settings() reads other settings from environment."""
        monkeypatch.setenv(
            "DATABASE_URL",
            "postgresql+asyncpg://user:pass@localhost:5432/testdb",
        )
        monkeypatch.setenv("DEBUG", "true")
        monkeypatch.setenv("DATABASE_POOL_SIZE", "50")

        result = get_settings()

        assert result.debug is True
        assert result.database_pool_size == 50


class TestSettingsValidation:
    """Tests for Settings validation."""

    def test_database_url_is_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that database_url is a required field."""
        monkeypatch.delenv("DATABASE_URL", raising=False)

        with pytest.raises(ValidationError):
            Settings()
