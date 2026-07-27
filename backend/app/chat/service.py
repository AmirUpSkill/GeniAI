from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.ai.provider import AIProvider, AIReply, FileCitation
from app.chat.repository import ChatRepository
from app.chat.schemas import ChatMessageCreate, ChatSessionCreate, ChatSessionUpdate, ChatTurnCreate
from app.core.errors import ChatSessionNotFoundError
from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.models.user import User
from app.file_search.service import FileSearchService


@dataclass(frozen=True)
class PreparedAITurn:
    chat_session: ChatSession
    user_message: ChatMessage
    messages: list[ChatMessage]
    document: object | None


@dataclass(frozen=True)
class ChatTextDelta:
    text: str


@dataclass(frozen=True)
class ChatTurnCompleted:
    assistant_message: ChatMessage


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
        turn = await self.prepare_ai_turn(current_user, chat_session_id, payload)
        document = turn.document
        reply = await self.ai_provider.generate_reply(
            turn.messages,
            getattr(document, "gemini_store_name", None),
        )
        # A small compatibility bridge keeps custom providers simple while the
        # application moves from string replies to evidence-bearing AIReply values.
        if isinstance(reply, str):
            reply = AIReply(text=reply)
        assistant_message = await self._save_assistant_reply(
            turn,
            reply.text,
            reply.citations,
        )
        return turn.user_message, assistant_message

    async def prepare_ai_turn(
        self,
        current_user: User,
        chat_session_id: str,
        payload: ChatTurnCreate,
    ) -> PreparedAITurn:
        chat_session = await self.get_session(current_user, chat_session_id)
        user_message = await self.repository.create_chat_message(
            chat_session,
            "user",
            payload.content,
        )
        await self.repository.session.commit()
        messages = await self.repository.list_chat_messages(chat_session.id)
        document = None
        if self.file_search_service is not None:
            document = await self.file_search_service.get_ready_document(
                current_user,
                chat_session.id,
            )
        return PreparedAITurn(
            chat_session=chat_session,
            user_message=user_message,
            messages=messages,
            document=document,
        )

    async def stream_ai_turn(
        self,
        turn: PreparedAITurn,
    ) -> AsyncIterator[ChatTextDelta | ChatTurnCompleted]:
        text_parts: list[str] = []
        citations: list[FileCitation] = []
        citation_keys: set[tuple[str | None, int | None, str]] = set()
        try:
            async for chunk in self.ai_provider.stream_reply(
                turn.messages,
                getattr(turn.document, "gemini_store_name", None),
            ):
                if chunk.text:
                    text_parts.append(chunk.text)
                    yield ChatTextDelta(text=chunk.text)
                for citation in chunk.citations:
                    key = (
                        citation.file_name,
                        citation.page_number,
                        " ".join(citation.source_excerpt.split()),
                    )
                    if key not in citation_keys:
                        citation_keys.add(key)
                        citations.append(citation)

            text = "".join(text_parts).strip()
            if not text:
                from app.core.errors import AIProviderError

                raise AIProviderError("AI provider returned an empty response.")
            assistant_message = await self._save_assistant_reply(
                turn,
                text,
                citations,
            )
            yield ChatTurnCompleted(assistant_message=assistant_message)
        except BaseException:
            await self.repository.session.rollback()
            raise

    async def _save_assistant_reply(
        self,
        turn: PreparedAITurn,
        text: str,
        citations: list[FileCitation],
    ) -> ChatMessage:
        assistant_message = await self.repository.create_chat_message(
            turn.chat_session,
            "assistant",
            text,
        )
        if self.file_search_service is not None and turn.document is not None:
            await self.file_search_service.save_citations(
                assistant_message,
                turn.document,
                citations,
            )
        await self.repository.session.commit()
        await self.repository.session.refresh(
            assistant_message,
            attribute_names=["file_search_citations"],
        )
        return assistant_message
