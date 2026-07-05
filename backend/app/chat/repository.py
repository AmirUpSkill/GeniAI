from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_chat_session(self, user_id: str, title: str) -> ChatSession:
        chat_session = ChatSession(user_id=user_id, title=title)
        self.session.add(chat_session)
        await self.session.flush()
        await self.session.refresh(chat_session)
        return chat_session

    async def list_chat_sessions(self, user_id: str) -> list[ChatSession]:
        result = await self.session.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_chat_session(self, user_id: str, chat_session_id: str) -> ChatSession | None:
        result = await self.session.execute(
            select(ChatSession).where(
                ChatSession.id == chat_session_id,
                ChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_chat_session_title(
        self,
        chat_session: ChatSession,
        title: str,
    ) -> ChatSession:
        chat_session.title = title
        chat_session.updated_at = datetime.now(UTC)
        await self.session.flush()
        await self.session.refresh(chat_session)
        return chat_session

    async def delete_chat_session(self, user_id: str, chat_session_id: str) -> None:
        await self.session.execute(
            delete(ChatSession).where(
                ChatSession.id == chat_session_id,
                ChatSession.user_id == user_id,
            )
        )

    async def create_chat_message(
        self,
        chat_session: ChatSession,
        role: str,
        content: str,
    ) -> ChatMessage:
        message = ChatMessage(
            chat_session_id=chat_session.id,
            role=role,
            content=content,
        )
        chat_session.updated_at = datetime.now(UTC)
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def list_chat_messages(self, chat_session_id: str) -> list[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.chat_session_id == chat_session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())
