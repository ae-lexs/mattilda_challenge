"""Application configuration using pydantic-settings.

This module centralizes all environment variable access. Configuration is
an infrastructure concern and should only be used in:
- Infrastructure layer (database, redis, external services)
- Entrypoints layer (FastAPI app composition)

Domain and Application layers must NOT import this module directly.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be overridden via environment variables.
    Variable names are case-insensitive (e.g., DATABASE_URL or database_url).

    Attributes:
        database_url: PostgreSQL connection string (async driver).
            Format: postgresql+asyncpg://user:pass@host:port/dbname
        database_pool_size: Connection pool size (default: 10).
        database_max_overflow: Max connections above pool_size (default: 20).
        redis_url: Redis connection string.
            Format: redis://host:port/db
        cache_ttl_seconds: Default cache TTL in seconds (default: 300).
        debug: Enable debug mode (SQL logging, etc.). Default: False.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars
    )

    # Database (PostgreSQL)
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Cache
    cache_ttl_seconds: int = 300

    # Application
    debug: bool = False
    app_version: str = "1.0.0"
    enable_metrics: bool = True

    @property
    def database_url_sync(self) -> str:
        """Return sync database URL for Alembic migrations.

        Alembic runs synchronously, so we need to replace the async driver
        (asyncpg) with the sync driver (psycopg2 or psycopg).

        Returns:
            Database URL with postgresql:// prefix (no async driver).
        """
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")


_settings: Settings | None = None


def get_settings() -> Settings:
    """Get application settings (lazy singleton).

    Settings are instantiated on first access, not at module import time.
    This allows tests to import the module without requiring environment
    variables to be set.

    Returns:
        Application settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
