"""Alembic migration environment configuration.

This module configures Alembic to work with the mattilda_challenge ORM models.
Per ADR-004 Section 8.1, Alembic runs synchronously even though the application
uses async SQLAlchemy.
"""

from __future__ import annotations

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Add src directory to Python path for importing mattilda_challenge modules
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import all models to register them with Base.metadata
# This import must come AFTER sys.path modification
from mattilda_challenge.infrastructure.postgres.models import (  # noqa: E402
    Base,
    InvoiceModel,
    PaymentModel,
    SchoolModel,
    StudentModel,
)

# Alembic Config object - provides access to values in alembic.ini
config = context.config

# Set up Python logging from the config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate support
# All models inherit from Base, so Base.metadata contains all table definitions
target_metadata = Base.metadata

# Ensure models are registered (prevents "unused import" warnings)
_models = [InvoiceModel, PaymentModel, SchoolModel, StudentModel]


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    so we don't need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate
    a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
