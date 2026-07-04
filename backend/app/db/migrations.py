from pathlib import Path

from alembic.config import Config


def get_backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_alembic_config_path() -> Path:
    return get_backend_root() / "alembic.ini"


def get_alembic_config() -> Config:
    return Config(str(get_alembic_config_path()))
