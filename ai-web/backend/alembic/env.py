"""Alembic environment configuration (minimal, uses DATABASE_URL env)."""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import MetaData, create_engine
from sqlalchemy import pool

from alembic import context

# Add the backend directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import Base  # noqa: E402
from app import models  # noqa: E402, F401  # Import models to register them with Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use Base.metadata for autogenerate support
target_metadata = Base.metadata


def _get_validated_target_metadata() -> MetaData | Sequence[MetaData]:
    """Ensure target_metadata is a populated MetaData or sequence of MetaData."""

    if target_metadata is None:
        raise RuntimeError(
            "Alembic target_metadata is None. Ensure models are imported and Base.metadata "
            "is defined so autogenerate can run."
        )

    if isinstance(target_metadata, MetaData):
        metadata_objects: Sequence[MetaData] = [target_metadata]
    elif isinstance(target_metadata, Sequence) and not isinstance(target_metadata, (str, bytes)):
        metadata_objects = list(target_metadata)
    else:
        raise RuntimeError(
            "Alembic target_metadata must be a sqlalchemy.MetaData or a sequence of MetaData. "
            f"Received type: {type(target_metadata).__name__}."
        )

    if not metadata_objects:
        raise RuntimeError("Alembic target_metadata sequence is empty; no metadata to inspect.")

    non_metadata_entries = [type(obj).__name__ for obj in metadata_objects if not isinstance(obj, MetaData)]
    if non_metadata_entries:
        raise RuntimeError(
            "Alembic target_metadata contains non-MetaData entries: "
            f"{', '.join(non_metadata_entries)}. Ensure Base.metadata is imported correctly."
        )

    table_details = []
    total_tables = 0
    for meta in metadata_objects:
        table_names = sorted(meta.tables.keys())
        total_tables += len(table_names)
        table_details.append(f"{len(table_names)} tables ({', '.join(table_names) if table_names else 'none'})")

    if total_tables == 0:
        detail = "; ".join(table_details)
        raise RuntimeError(
            "Alembic target_metadata has no tables; models may not be imported. "
            f"Metadata table summary: {detail}."
        )

    # Return a MetaData if only one item exists so Alembic gets the expected type
    return metadata_objects[0] if len(metadata_objects) == 1 else metadata_objects


def _get_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        return ini_url

    raise RuntimeError(
        "No database URL configured. Set DATABASE_URL or "
        "define sqlalchemy.url in alembic.ini."
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    validated_metadata = _get_validated_target_metadata()
    url = _get_database_url()

    context.configure(
        url=url,
        target_metadata=validated_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    validated_metadata = _get_validated_target_metadata()
    url = _get_database_url()

    connectable = create_engine(url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=validated_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
