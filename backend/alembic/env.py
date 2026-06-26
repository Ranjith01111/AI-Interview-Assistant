"""
Alembic Environment Configuration

Supports both synchronous (offline) and asynchronous (online) migrations.
Reads the database URL from the application settings.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Import application models so metadata is populated ───────────────
# This must come BEFORE we reference target_metadata.
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.db.base import Base
from backend.models.interview import InterviewSession  # noqa: F401
from backend.models.question import Question            # noqa: F401
from backend.models.answer import Answer                # noqa: F401
from backend.models.user import User                    # noqa: F401
from backend.models.audit_log import AuditLog          # noqa: F401
from backend.models.resume import Resume                # noqa: F401
from backend.models.proctor_log import ProctorLog      # noqa: F401
from backend.models.analytics import Analytics          # noqa: F401
from backend.core.config import settings

# ── Alembic Config object ───────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the target metadata for autogenerate support
target_metadata = Base.metadata

# Override sqlalchemy.url from application settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


# ── Offline migrations (generate SQL without a live DB) ──────────────

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This emits SQL to stdout rather than connecting to a database.
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


# ── Online (async) migrations ────────────────────────────────────────

def do_run_migrations(connection: Connection) -> None:
    """Helper that runs within a sync context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using an async engine."""
    asyncio.run(run_async_migrations())


# ── Entry point ──────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
