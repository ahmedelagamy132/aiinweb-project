"""Alembic environment configuration (minimal, uses DATABASE_URL env)."""

from __future__ import annotations

import os
from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No autogenerate needed yet → metadata can be None
target_metadata = None


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "In docker-compose it should be like: "
            "postgresql+psycopg2://aiweb:aiweb@db:5432/aiweb"
        )
    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = _get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = _get_database_url()

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
