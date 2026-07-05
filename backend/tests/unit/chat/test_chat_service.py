from datetime import UTC, datetime
from typing import cast

import pytest

from app.ai.provider import AIProvider
from app.chat.repository import ChatRepository
from app.chat.schemas import ChatMessageCreate, ChatSessionCreate, ChatSessionUpdate, ChatTurnCreate
from app.chat.service import ChatService
from app.core.errors import ChatSessionNotFoundError
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


class FakeChatRepository:
    def __init__(self, chat_session: ChatSession | None = None) -> None:
        self.session = FakeSession()
        self.chat_session = chat_session
        self.deleted_id: str | None = None
        self.messages: list[ChatMessage] = []

    async def create_chat_session(self, user_id: str, title: str) -> ChatSession:
        self.chat_session = ChatSession(
            id="chat_new",
            user_id=user_id,
            title=title,
            summary=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return self.chat_session

    async def list_chat_sessions(self, user_id: str) -> list[ChatSession]:
        if self.chat_session is None or self.chat_session.user_id != user_id:
            return []
        return [self.chat_session]

    async def get_chat_session(self, user_id: str, chat_session_id: str) -> ChatSession | None:
        if (
            self.chat_session is not None
            and self.chat_session.user_id == user_id
            and self.chat_session.id == chat_session_id
        ):
            return self.chat_session
        return None

    async def update_chat_session_title(
        self,
        chat_session: ChatSession,
        title: str,
    ) -> ChatSession:
        chat_session.title = title
        return chat_session

    async def delete_chat_session(self, user_id: str, chat_session_id: str) -> None:
        _ = user_id
        self.deleted_id = chat_session_id

    async def create_chat_message(
        self,
        chat_session: ChatSession,
        role: str,
        content: str,
    ) -> ChatMessage:
        message = ChatMessage(
            id="msg_new",
            chat_session_id=chat_session.id,
            role=role,
            content=content,
            created_at=datetime.now(UTC),
        )
        self.messages.append(message)
        return message

    async def list_chat_messages(self, chat_session_id: str) -> list[ChatMessage]:
        return [message for message in self.messages if message.chat_session_id == chat_session_id]


class FakeAIProvider:
    async def generate_reply(self, messages: list[ChatMessage]) -> str:
        _ = messages
        return "AI reply"


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


def build_chat_session(user_id: str = "usr_123") -> ChatSession:
    return ChatSession(
        id="chat_123",
        user_id=user_id,
        title="Original title",
        summary=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def build_service(repository: FakeChatRepository) -> ChatService:
    return ChatService(cast(ChatRepository, repository), cast(AIProvider, FakeAIProvider()))


@pytest.mark.asyncio
async def test_create_session_commits_new_chat() -> None:
    repository = FakeChatRepository()
    service = build_service(repository)

    chat_session = await service.create_session(
        build_user(),
        ChatSessionCreate(title="Planning"),
    )

    assert chat_session.title == "Planning"
    assert chat_session.user_id == "usr_123"
    assert repository.session.committed is True


@pytest.mark.asyncio
async def test_update_session_rejects_missing_or_other_user_chat() -> None:
    repository = FakeChatRepository(chat_session=build_chat_session(user_id="usr_other"))
    service = build_service(repository)

    with pytest.raises(ChatSessionNotFoundError):
        await service.update_session(
            build_user(),
            "chat_123",
            ChatSessionUpdate(title="Renamed"),
        )


@pytest.mark.asyncio
async def test_create_message_commits_to_owned_chat() -> None:
    repository = FakeChatRepository(chat_session=build_chat_session())
    service = build_service(repository)

    message = await service.create_message(
        build_user(),
        "chat_123",
        ChatMessageCreate(role="user", content="Hello"),
    )

    assert message.chat_session_id == "chat_123"
    assert message.content == "Hello"
    assert repository.session.committed is True


@pytest.mark.asyncio
async def test_delete_session_commits_owned_chat_delete() -> None:
    repository = FakeChatRepository(chat_session=build_chat_session())
    service = build_service(repository)

    await service.delete_session(build_user(), "chat_123")

    assert repository.deleted_id == "chat_123"
    assert repository.session.committed is True


@pytest.mark.asyncio
async def test_create_ai_turn_saves_user_and_assistant_messages() -> None:
    repository = FakeChatRepository(chat_session=build_chat_session())
    service = build_service(repository)

    user_message, assistant_message = await service.create_ai_turn(
        build_user(),
        "chat_123",
        ChatTurnCreate(content="Write a launch plan"),
    )

    assert user_message.role == "user"
    assert user_message.content == "Write a launch plan"
    assert assistant_message.role == "assistant"
    assert assistant_message.content == "AI reply"
    assert repository.session.committed is True
