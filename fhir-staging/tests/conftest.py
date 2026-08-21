import os

# Must be set before any app module is imported so pydantic-settings reads them.
os.environ.setdefault("STAGING_DATABASE_URL", "sqlite+aiosqlite:///:memory:")

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import BigInteger, Sequence as SASequence, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import StagingBase
from app.main import app, container, mount_routers  # triggers model + router imports

# Router mounting happens inside app.main's lifespan (at real ASGI startup), but
# httpx's ASGITransport never runs the ASGI lifespan protocol. Mount once here
# instead — mount_routers() only registers routes, no async/DB side effects.
mount_routers(app)


# ── Sequence simulation ───────────────────────────────────────────────────────
# PostgreSQL sequences don't exist in SQLite. Strip the server_default (which
# would emit nextval() DDL) and assign from an in-process counter in the ORM
# before_insert event instead.

_seq_counters: dict[str, int] = {}
_defaults_stripped = False


def _strip_server_defaults() -> None:
    """Remove nextval() server_defaults once, before create_all().

    func.now() server_defaults (created_at) are left intact — SQLite compiles
    those to CURRENT_TIMESTAMP just fine.
    """
    global _defaults_stripped
    if _defaults_stripped:
        return
    for table in StagingBase.metadata.tables.values():
        for col in table.columns:
            sd = col.server_default
            if sd is None:
                continue
            arg = getattr(sd, "arg", None)
            if arg is not None and type(arg).__name__ == "next_value":
                col.server_default = None
    _defaults_stripped = True


@event.listens_for(StagingBase, "before_insert", propagate=True)
def _simulate_sequence(mapper, connection, target) -> None:
    """Assign sequence-based public ids from a per-sequence Python counter.

    When a Sequence is passed as a positional Column arg, SQLAlchemy stores it
    directly as col.default (a Sequence instance, NOT wrapped in
    ColumnDefault) — hence the isinstance check.
    """
    for col in mapper.local_table.columns:
        if isinstance(col.default, SASequence):
            if getattr(target, col.name, None) is None:
                seq: SASequence = col.default
                key = seq.name
                if key not in _seq_counters:
                    _seq_counters[key] = seq.start or 1
                else:
                    _seq_counters[key] += seq.increment or 1
                setattr(target, col.name, _seq_counters[key])


_pk_counters: dict[str, int] = {}


@event.listens_for(StagingBase, "before_insert", propagate=True)
def _simulate_bigint_pk(mapper, connection, target) -> None:
    """SQLite's implicit rowid-alias autoincrement only applies to a primary
    key whose DDL literally reads INTEGER PRIMARY KEY. BigInteger compiles to
    BIGINT, which doesn't get that treatment, so it stays NULL on insert (NOT
    NULL failure) unless simulated here the same way sequences are above.
    Every `id` in this schema is BigInteger, so this covers all 18 tables."""
    pk_cols = list(mapper.local_table.primary_key.columns)
    if len(pk_cols) != 1:
        return
    col = pk_cols[0]
    if not isinstance(col.type, BigInteger):
        return
    if getattr(target, col.name, None) is not None:
        return
    key = mapper.local_table.name
    _pk_counters[key] = _pk_counters.get(key, 0) + 1
    setattr(target, col.name, _pk_counters[key])


@pytest.fixture(autouse=True)
def _reset_counters():
    """Each test gets its own database, so the id counters must reset with it —
    otherwise ids leak across tests and assertions on specific values (10000,
    20000) depend on execution order."""
    _seq_counters.clear()
    _pk_counters.clear()
    yield


# ── TestDatabase ──────────────────────────────────────────────────────────────


class TestDatabase:
    """Drop-in replacement for app.core.database.Database using a pre-built engine."""

    def __init__(self, engine):
        self.engine = engine
        self.session_maker = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def disconnect(self) -> None:
        pass  # lifecycle is managed by the fixture

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        session: AsyncSession = self.session_maker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
async def _engine():
    """Single in-memory SQLite engine per test (StaticPool -> one connection)."""
    _strip_server_defaults()
    eng = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with eng.begin() as conn:
        await conn.run_sync(StagingBase.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def client(_engine):
    test_db = TestDatabase(_engine)
    container.core.database.override(test_db)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    container.core.database.reset_override()


BASE = "/api/v1/staging-records/"
