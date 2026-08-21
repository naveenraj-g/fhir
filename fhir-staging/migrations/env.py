import asyncio
import os
import sys
from logging.config import fileConfig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import StagingBase so Alembic can see all table metadata
from app.core.database import StagingBase

# Import every model module so SQLAlchemy registers the tables on the metadata
import app.models  # noqa: F401

# Read alembic.ini logging config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Pull DB URL from app settings so it matches the running app exactly
from app.core.config import settings

config.set_main_option("sqlalchemy.url", settings.STAGING_DATABASE_URL)

target_metadata = StagingBase.metadata


def process_revision_directives(context, revision, directives):
    """Inject CREATE SEQUENCE / DROP SEQUENCE for every Sequence bound to the metadata.

    Alembic's autogenerate does not emit sequence DDL on its own, but both
    public-ID columns here (`staging_medical_record.staging_medical_record_id`,
    `staging_observation.observation_id`) carry a server_default of nextval(), so the
    sequence has to exist before the table is created.
    """
    from alembic.operations import ops as alembic_ops

    sequences = sorted(target_metadata._sequences.values(), key=lambda s: s.name)
    if not sequences or not directives:
        return

    script = directives[0]

    create_ops = [
        alembic_ops.ExecuteSQLOp(
            f"CREATE SEQUENCE IF NOT EXISTS {seq.name}"
            f" START {seq.start} INCREMENT {seq.increment}"
        )
        for seq in sequences
    ]
    script.upgrade_ops.ops = create_ops + list(script.upgrade_ops.ops)

    drop_ops = [
        alembic_ops.ExecuteSQLOp(f"DROP SEQUENCE IF EXISTS {seq.name}")
        for seq in sequences
    ]
    script.downgrade_ops.ops = list(script.downgrade_ops.ops) + drop_ops


def run_migrations_offline() -> None:
    """Generate SQL script without a live DB connection (useful for review/CI)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations against the live DB using the async engine."""
    engine = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
