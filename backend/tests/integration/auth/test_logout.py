from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_auth_service
from app.core.config import Settings, get_settings
from app.main import create_app


class FakeAuthService:
    def __init__(self) -> None:
        self.logged_out_token: str | None = None

    async def logout(self, raw_token: str | None) -> None:
        self.logged_out_token = raw_token


@pytest.fixture
def app() -> Generator[FastAPI, None, None]:
    app = create_app()
    yield app
    app.dependency_overrides.clear()


def test_logout_deletes_session_and_clears_cookie(app: FastAPI) -> None:
    fake_service = FakeAuthService()
    settings = Settings(SESSION_COOKIE_NAME="geni_session", _env_file=None)

    def override_settings() -> Settings:
        return settings

    def override_auth_service() -> FakeAuthService:
        return fake_service

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_auth_service] = override_auth_service
    client = TestClient(app)

    response = client.post("/api/auth/logout", cookies={"geni_session": "raw-session-token"})

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "User logged out successfully.",
    }
    assert fake_service.logged_out_token == "raw-session-token"
    assert "geni_session=" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
