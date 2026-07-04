from app.core.config import Settings


def test_database_url_uses_async_postgresql_driver() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url.startswith("postgresql+asyncpg://")
