from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


AppEnv = Literal["local", "test", "development", "production"]


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

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
