from app.ai.provider import AIProvider, AIReply
from app.chat.repository import ChatRepository
from app.chat.schemas import ChatMessageCreate, ChatSessionCreate, ChatSessionUpdate, ChatTurnCreate
from app.core.errors import ChatSessionNotFoundError
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User
from app.file_search.service import FileSearchService


class ChatService:
    def __init__(
        self,
        repository: ChatRepository,
        ai_provider: AIProvider,
        file_search_service: FileSearchService | None = None,
    ) -> None:
        self.repository = repository
        self.ai_provider = ai_provider
        self.file_search_service = file_search_service

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
        if self.file_search_service is not None:
            await self.file_search_service.delete_for_chat_session_if_present(
                current_user,
                chat_session.id,
            )
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
        document = None
        if self.file_search_service is not None:
            document = await self.file_search_service.get_ready_document(
                current_user,
                chat_session.id,
            )
        reply = await self.ai_provider.generate_reply(
            messages,
            document.gemini_store_name if document is not None else None,
        )
        # A small compatibility bridge keeps custom providers simple while the
        # application moves from string replies to evidence-bearing AIReply values.
        if isinstance(reply, str):
            reply = AIReply(text=reply)
        assistant_message = await self.repository.create_chat_message(
            chat_session,
            "assistant",
            reply.text,
        )
        if self.file_search_service is not None and document is not None:
            await self.file_search_service.save_citations(
                assistant_message,
                document,
                reply.citations,
            )
        await self.repository.session.commit()
        await self.repository.session.refresh(
            assistant_message,
            attribute_names=["file_search_citations"],
        )
        return user_message, assistant_message
