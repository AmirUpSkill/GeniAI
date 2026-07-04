from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.main import create_app
from app.models.user import User


@pytest.fixture
def app() -> Generator[FastAPI, None, None]:
    app = create_app()
    yield app
    app.dependency_overrides.clear()


def test_profile_me_returns_safe_profile_data(app: FastAPI) -> None:
    async def override_current_user() -> User:
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

    app.dependency_overrides[get_current_user] = override_current_user
    client = TestClient(app)

    response = client.get("/api/profile/me")

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["email"] == "amir@example.com"
    assert payload["fullName"] == "Amir Abdallah"
    assert "providerUserId" not in payload
    assert "sessionTokenHash" not in payload
