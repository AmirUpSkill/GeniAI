from collections.abc import Generator
from datetime import UTC, datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.chat.dependencies import get_chat_service
from app.core.errors import ChatSessionNotFoundError
from app.main import create_app
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User


class FakeChatService:
    def __init__(self) -> None:
        self.chat_session = ChatSession(
            id="chat_123",
            user_id="usr_123",
            title="First chat",
            summary=None,
            created_at=datetime(2026, 7, 5, 12, 0, tzinfo=UTC),
            updated_at=datetime(2026, 7, 5, 12, 1, tzinfo=UTC),
        )
        self.message = ChatMessage(
            id="msg_123",
            chat_session_id="chat_123",
            role="user",
            content="Hello Geni",
            created_at=datetime(2026, 7, 5, 12, 2, tzinfo=UTC),
        )
        self.assistant_message = ChatMessage(
            id="msg_456",
            chat_session_id="chat_123",
            role="assistant",
            content="Hello from Gemini",
            created_at=datetime(2026, 7, 5, 12, 3, tzinfo=UTC),
        )

    async def create_session(self, current_user: User, payload: object) -> ChatSession:
        _ = (current_user, payload)
        return self.chat_session

    async def list_sessions(self, current_user: User) -> list[ChatSession]:
        _ = current_user
        return [self.chat_session]

    async def get_session(self, current_user: User, chat_session_id: str) -> ChatSession:
        _ = current_user
        if chat_session_id != self.chat_session.id:
            raise ChatSessionNotFoundError()
        return self.chat_session

    async def update_session(
        self,
        current_user: User,
        chat_session_id: str,
        payload: object,
    ) -> ChatSession:
        _ = current_user
        if chat_session_id != self.chat_session.id:
            raise ChatSessionNotFoundError()
        self.chat_session.title = getattr(payload, "title")
        return self.chat_session

    async def delete_session(self, current_user: User, chat_session_id: str) -> None:
        _ = current_user
        if chat_session_id != self.chat_session.id:
            raise ChatSessionNotFoundError()

    async def create_message(
        self,
        current_user: User,
        chat_session_id: str,
        payload: object,
    ) -> ChatMessage:
        _ = current_user
        if chat_session_id != self.chat_session.id:
            raise ChatSessionNotFoundError()
        self.message.role = getattr(payload, "role")
        self.message.content = getattr(payload, "content")
        return self.message

    async def list_messages(self, current_user: User, chat_session_id: str) -> list[ChatMessage]:
        _ = current_user
        if chat_session_id != self.chat_session.id:
            raise ChatSessionNotFoundError()
        return [self.message]

    async def create_ai_turn(
        self,
        current_user: User,
        chat_session_id: str,
        payload: object,
    ) -> tuple[ChatMessage, ChatMessage]:
        _ = current_user
        if chat_session_id != self.chat_session.id:
            raise ChatSessionNotFoundError()
        self.message.content = getattr(payload, "content")
        return self.message, self.assistant_message


def build_user() -> User:
    return User(
        id="usr_123",
        email="amir@example.com",
        full_name="Amir Abdallah",
        avatar_url=None,
        provider="google",
        provider_user_id="google_123",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def app() -> Generator[FastAPI, None, None]:
    app = create_app()

    async def override_current_user() -> User:
        return build_user()

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_chat_service] = FakeChatService
    yield app
    app.dependency_overrides.clear()


def test_create_chat_session(app: FastAPI) -> None:
    client = TestClient(app)

    response = client.post("/api/chat/sessions", json={"title": "First chat"})

    assert response.status_code == 201
    assert response.json()["data"]["id"] == "chat_123"
    assert response.json()["data"]["title"] == "First chat"
    assert "createdAt" in response.json()["data"]


def test_list_chat_sessions(app: FastAPI) -> None:
    client = TestClient(app)

    response = client.get("/api/chat/sessions")

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "chat_123"


def test_update_chat_session(app: FastAPI) -> None:
    client = TestClient(app)

    response = client.patch("/api/chat/sessions/chat_123", json={"title": "Renamed"})

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Renamed"


def test_create_and_list_chat_messages(app: FastAPI) -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/chat/sessions/chat_123/messages",
        json={"role": "user", "content": "Hello Geni"},
    )
    list_response = client.get("/api/chat/sessions/chat_123/messages")

    assert create_response.status_code == 201
    assert create_response.json()["data"]["chatSessionId"] == "chat_123"
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["content"] == "Hello Geni"


def test_create_chat_turn_returns_user_and_assistant_messages(app: FastAPI) -> None:
    client = TestClient(app)

    response = client.post(
        "/api/chat/sessions/chat_123/turns",
        json={"content": "Hello Gemini"},
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["userMessage"]["content"] == "Hello Gemini"
    assert payload["assistantMessage"]["role"] == "assistant"
    assert payload["assistantMessage"]["content"] == "Hello from Gemini"


def test_delete_chat_session(app: FastAPI) -> None:
    client = TestClient(app)

    response = client.delete("/api/chat/sessions/chat_123")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Chat session deleted successfully.",
    }


def test_missing_chat_session_returns_404(app: FastAPI) -> None:
    client = TestClient(app)

    response = client.get("/api/chat/sessions/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "CHAT_SESSION_NOT_FOUND"
