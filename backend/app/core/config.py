from functools import lru_cache
from typing import Any
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


AppEnv = Literal["local", "test", "development", "production"]
CookieSameSite = Literal["lax", "strict", "none"]


class Settings(BaseSettings):
    # --- Application ---
    app_name: str = Field(default="Geni", alias="APP_NAME")
    app_env: AppEnv = Field(default="local", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    api_prefix: str = Field(default="/api", alias="API_PREFIX")

    # --- Database ---
    postgres_user: str = Field(default="geni", alias="POSTGRES_USER")
    postgres_password: str = Field(default="geni_password", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="geni", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_url: str = Field(
        default="postgresql+asyncpg://geni:geni_password@localhost:5432/geni",
        alias="DATABASE_URL",
    )

    # --- Auth ---
    google_client_id: str = Field(default="local-google-client-id", alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(
        default="local-google-client-secret",
        alias="GOOGLE_CLIENT_SECRET",
    )
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/auth/google/callback",
        alias="GOOGLE_REDIRECT_URI",
    )
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")

    # --- AI Provider ---
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-3.1-flash-lite", alias="GEMINI_MODEL")

    # --- Session Cookie ---
    session_cookie_name: str = Field(default="geni_session", alias="SESSION_COOKIE_NAME")
    session_secret_key: str = Field(default="change-me-in-production", alias="SESSION_SECRET_KEY")
    session_ttl_days: int = Field(default=7, alias="SESSION_TTL_DAYS")
    session_cookie_secure: bool = Field(default=False, alias="SESSION_COOKIE_SECURE")
    session_cookie_samesite: CookieSameSite = Field(default="lax", alias="SESSION_COOKIE_SAMESITE")

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    def __init__(self, **values: Any) -> None:
        super().__init__(**values)


@lru_cache
def get_settings() -> Settings:
    return Settings()
