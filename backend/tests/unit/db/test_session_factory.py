import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.db.migrations import get_alembic_config, get_alembic_config_path
from app.db.session import create_database_engine, get_db_session


@pytest.mark.asyncio
async def test_create_database_engine_uses_settings_database_url() -> None:
    settings = Settings(
        DATABASE_URL="postgresql+asyncpg://test_user:test_password@localhost:5432/test_db",
        _env_file=None,
    )

    engine = create_database_engine(settings)

    try:
        assert isinstance(engine, AsyncEngine)
        assert str(engine.url) == "postgresql+asyncpg://test_user:***@localhost:5432/test_db"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_async_sessionmaker_can_be_configured_from_engine() -> None:
    settings = Settings(_env_file=None)
    engine = create_database_engine(settings)

    try:
        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

        assert session_factory.kw["bind"] is engine
        assert session_factory.kw["expire_on_commit"] is False
        assert session_factory.kw["autoflush"] is False
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_get_db_session_yields_async_session() -> None:
    session_generator = get_db_session()

    session = await anext(session_generator)

    try:
        assert isinstance(session, AsyncSession)
    finally:
        await session_generator.aclose()


def test_alembic_config_points_to_backend_alembic_ini() -> None:
    config_path = get_alembic_config_path()
    config = get_alembic_config()

    assert config_path.name == "alembic.ini"
    assert config_path.exists()
    assert config.config_file_name == str(config_path)
