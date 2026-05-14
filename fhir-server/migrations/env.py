import asyncio
import os
import sys
from logging.config import fileConfig

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# Import FHIRBase so Alembic can see all table metadata
from app.core.database import FHIRBase

# Import every model module so SQLAlchemy registers the tables on FHIRBase.metadata
import app.models.patient  # noqa: F401
import app.models.practitioner  # noqa: F401
import app.models.encounter.encounter  # noqa: F401
import app.models.appointment.appointment  # noqa: F401
import app.models.questionnaire_response.questionnaire_response  # noqa: F401
import app.models.vitals.vitals  # noqa: F401
import app.models.service_request.service_request  # noqa: F401
import app.models.medication_request.medication_request  # noqa: F401
import app.models.procedure.procedure  # noqa: F401
import app.models.diagnostic_report.diagnostic_report  # noqa: F401
import app.models.condition.condition  # noqa: F401
import app.models.device_request.device_request  # noqa: F401

# Read alembic.ini logging config
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Pull DB URL from app settings so it matches the running app exactly
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.FHIR_DATABASE_URL)

target_metadata = FHIRBase.metadata


def run_migrations_offline() -> None:
    """Generate SQL script without a live DB connection (useful for review/CI)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
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
