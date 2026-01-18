"""Fixtures for unit tests.

Sets up required environment variables before importing application modules.
"""

from __future__ import annotations

import os

# Set required environment variables before any application imports
# These are needed because some modules call get_settings() at import time
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
