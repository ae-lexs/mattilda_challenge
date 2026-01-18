"""Tests for application configuration."""

from __future__ import annotations

from mattilda_challenge.config import Settings


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
