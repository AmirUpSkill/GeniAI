from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings

# -----------------------------------------------------------------------------
# Engine Factory — builds a new AsyncEngine from Settings
# -----------------------------------------------------------------------------


def create_database_engine(settings: Settings | None = None) -> AsyncEngine:
    resolved_settings = settings or get_settings()
    return create_async_engine(
        resolved_settings.database_url,
        pool_pre_ping=True,
    )


# -----------------------------------------------------------------------------
# Global Engine & Session Factory — module-level singletons
# -----------------------------------------------------------------------------

engine: AsyncEngine = create_database_engine()
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# -----------------------------------------------------------------------------
# FastAPI Dependency — yields one AsyncSession per HTTP request
# -----------------------------------------------------------------------------


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
