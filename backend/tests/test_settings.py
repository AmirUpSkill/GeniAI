from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_settings_load_without_env_file() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "Geni"
    assert settings.app_env == "local"
    assert settings.debug is True
    assert settings.api_prefix == "/api"
    assert settings.database_url == "postgresql+asyncpg://geni:geni_password@localhost:5432/geni"
    assert settings.google_client_id == "local-google-client-id"
    assert settings.session_cookie_name == "geni_session"
    assert settings.session_ttl_days == 7


def test_env_file_values_override_defaults(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "APP_NAME=Geni Test",
                "APP_ENV=test",
                "DEBUG=false",
                "API_PREFIX=/test-api",
                "POSTGRES_USER=test_user",
                "POSTGRES_PASSWORD=test_password",
                "POSTGRES_DB=test_db",
                "POSTGRES_HOST=postgres",
                "POSTGRES_PORT=5544",
                "DATABASE_URL=postgresql+asyncpg://test_user:test_password@postgres:5544/test_db",
                "GOOGLE_CLIENT_ID=test-client-id",
                "GOOGLE_CLIENT_SECRET=test-client-secret",
                "GOOGLE_REDIRECT_URI=http://localhost:8000/test-callback",
                "FRONTEND_URL=http://localhost:5173",
                "SESSION_COOKIE_NAME=test_session",
                "SESSION_SECRET_KEY=test-secret-key",
                "SESSION_TTL_DAYS=14",
                "SESSION_COOKIE_SECURE=true",
                "SESSION_COOKIE_SAMESITE=strict",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.app_name == "Geni Test"
    assert settings.app_env == "test"
    assert settings.debug is False
    assert settings.api_prefix == "/test-api"
    assert settings.postgres_user == "test_user"
    assert settings.postgres_password == "test_password"
    assert settings.postgres_db == "test_db"
    assert settings.postgres_host == "postgres"
    assert settings.postgres_port == 5544
    assert settings.database_url == "postgresql+asyncpg://test_user:test_password@postgres:5544/test_db"
    assert settings.google_client_id == "test-client-id"
    assert settings.google_client_secret == "test-client-secret"
    assert settings.google_redirect_uri == "http://localhost:8000/test-callback"
    assert settings.frontend_url == "http://localhost:5173"
    assert settings.session_cookie_name == "test_session"
    assert settings.session_secret_key == "test-secret-key"
    assert settings.session_ttl_days == 14
    assert settings.session_cookie_secure is True
    assert settings.session_cookie_samesite == "strict"


@pytest.mark.parametrize("app_env", ["local", "test", "development", "production"])
def test_app_env_accepts_supported_values(app_env: str) -> None:
    settings = Settings(APP_ENV=app_env, _env_file=None)

    assert settings.app_env == app_env


def test_app_env_rejects_unknown_values() -> None:
    with pytest.raises(ValidationError):
        Settings(APP_ENV="staging", _env_file=None)
