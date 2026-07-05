from app.ai.provider import AIProvider
from app.chat.repository import ChatRepository
from app.chat.schemas import ChatMessageCreate, ChatSessionCreate, ChatSessionUpdate, ChatTurnCreate
from app.core.errors import ChatSessionNotFoundError
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User


class ChatService:
    def __init__(self, repository: ChatRepository, ai_provider: AIProvider) -> None:
        self.repository = repository
        self.ai_provider = ai_provider

    async def create_session(self, current_user: User, payload: ChatSessionCreate) -> ChatSession:
        chat_session = await self.repository.create_chat_session(current_user.id, payload.title)
        await self.repository.session.commit()
        return chat_session

    async def list_sessions(self, current_user: User) -> list[ChatSession]:
        return await self.repository.list_chat_sessions(current_user.id)

    async def get_session(self, current_user: User, chat_session_id: str) -> ChatSession:
        chat_session = await self.repository.get_chat_session(current_user.id, chat_session_id)
        if chat_session is None:
            raise ChatSessionNotFoundError()
        return chat_session

    async def update_session(
        self,
        current_user: User,
        chat_session_id: str,
        payload: ChatSessionUpdate,
    ) -> ChatSession:
        chat_session = await self.get_session(current_user, chat_session_id)
        updated = await self.repository.update_chat_session_title(chat_session, payload.title)
        await self.repository.session.commit()
        return updated

    async def delete_session(self, current_user: User, chat_session_id: str) -> None:
        chat_session = await self.get_session(current_user, chat_session_id)
        await self.repository.delete_chat_session(current_user.id, chat_session.id)
        await self.repository.session.commit()

    async def create_message(
        self,
        current_user: User,
        chat_session_id: str,
        payload: ChatMessageCreate,
    ) -> ChatMessage:
        chat_session = await self.get_session(current_user, chat_session_id)
        message = await self.repository.create_chat_message(
            chat_session,
            payload.role,
            payload.content,
        )
        await self.repository.session.commit()
        return message

    async def list_messages(
        self,
        current_user: User,
        chat_session_id: str,
    ) -> list[ChatMessage]:
        chat_session = await self.get_session(current_user, chat_session_id)
        return await self.repository.list_chat_messages(chat_session.id)

    async def create_ai_turn(
        self,
        current_user: User,
        chat_session_id: str,
        payload: ChatTurnCreate,
    ) -> tuple[ChatMessage, ChatMessage]:
        chat_session = await self.get_session(current_user, chat_session_id)
        user_message = await self.repository.create_chat_message(
            chat_session,
            "user",
            payload.content,
        )
        messages = await self.repository.list_chat_messages(chat_session.id)
        assistant_content = await self.ai_provider.generate_reply(messages)
        assistant_message = await self.repository.create_chat_message(
            chat_session,
            "assistant",
            assistant_content,
        )
        await self.repository.session.commit()
        return user_message, assistant_message
