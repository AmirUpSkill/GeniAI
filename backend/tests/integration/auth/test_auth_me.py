from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.core.errors import AuthUnauthorizedError
from app.main import create_app
from app.models.user import User


def build_user() -> User:
    return User(
        id="usr_123",
        email="amir@example.com",
        full_name="Amir Abdallah",
        avatar_url="https://example.com/avatar.png",
        provider="google",
        provider_user_id="google_secret",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def app() -> Generator[FastAPI, None, None]:
    app = create_app()
    yield app
    app.dependency_overrides.clear()


def test_auth_me_returns_current_user(app: FastAPI) -> None:
    async def override_current_user() -> User:
        return build_user()

    app.dependency_overrides[get_current_user] = override_current_user
    client = TestClient(app)

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    assert response.json()["data"]["email"] == "amir@example.com"
    assert response.json()["data"]["fullName"] == "Amir Abdallah"


def test_auth_me_returns_401_without_session(app: FastAPI) -> None:
    async def override_current_user() -> User:
        raise AuthUnauthorizedError()

    app.dependency_overrides[get_current_user] = override_current_user
    client = TestClient(app)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {
        "success": False,
        "error": {
            "code": "AUTH_UNAUTHORIZED",
            "message": "User is not authenticated.",
        },
    }
