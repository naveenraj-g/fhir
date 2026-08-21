from dependency_injector import containers, providers

from app.core.config import settings
from app.core.database import Database


class CoreContainer(containers.DeclarativeContainer):
    # Singleton database — one engine and connection pool per process.
    database = providers.Singleton(
        Database,
        db_url=settings.STAGING_DATABASE_URL,
    )
