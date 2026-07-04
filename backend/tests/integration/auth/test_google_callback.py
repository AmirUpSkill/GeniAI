from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_auth_service
from app.core.config import Settings, get_settings
from app.main import create_app
from app.models.user import User


class FakeAuthService:
    async def authenticate_google_callback(self, code: str) -> tuple[User, str]:
        assert code == "valid-code"
        return (
            User(
                id="usr_123",
                email="amir@example.com",
                full_name="Amir Abdallah",
                avatar_url=None,
                provider="google",
                provider_user_id="google_secret",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
            "raw-session-token",
        )


@pytest.fixture
def app() -> Generator[FastAPI, None, None]:
    app = create_app()
    yield app
    app.dependency_overrides.clear()


def test_google_callback_redirects_and_sets_session_cookie(app: FastAPI) -> None:
    settings = Settings(
        FRONTEND_URL="http://localhost:3000",
        SESSION_COOKIE_NAME="geni_session",
        SESSION_COOKIE_SECURE=False,
        _env_file=None,
    )

    def override_settings() -> Settings:
        return settings

    def override_auth_service() -> FakeAuthService:
        return FakeAuthService()

    app.dependency_overrides[get_settings] = override_settings
    app.dependency_overrides[get_auth_service] = override_auth_service
    client = TestClient(app)

    response = client.get("/api/auth/google/callback?code=valid-code", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "http://localhost:3000/chat"
    assert "geni_session=raw-session-token" in response.headers["set-cookie"]
    assert "HttpOnly" in response.headers["set-cookie"]
