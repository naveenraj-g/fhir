from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
from contextlib import asynccontextmanager
from app.core.logging import get_logger
from typing import AsyncGenerator
from sqlalchemy import text

logger = get_logger(__name__)

FHIRBase = declarative_base()


class Database:
    def __init__(self, db_url: str):
        self.engine = create_async_engine(db_url, echo=False)

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def connect(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(FHIRBase.metadata.create_all)

    async def disconnect(self):
        await self.engine.dispose()

    async def reset(self):
        if settings.ENVIRONMENT == "production":
            raise RuntimeError("Database reset is not allowed in production.")

        logger.warning("Resetting database: dropping all tables...")

        async with self.engine.begin() as conn:
            # await conn.execute(text("DROP SCHEMA public CASCADE"))
            # await conn.execute(text("CREATE SCHEMA public"))
            await conn.run_sync(FHIRBase.metadata.drop_all)
            await conn.run_sync(FHIRBase.metadata.create_all)

        logger.warning("Database reset complete.")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        session: AsyncSession = self.session_maker()

        try:
            yield session
        except Exception:
            logger.exception("Session rollback because of exception")
            await session.rollback()
            raise
        finally:
            await session.close()
