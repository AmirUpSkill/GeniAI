from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gemini_provider import GeminiProvider
from app.ai.provider import AIProvider
from app.chat.repository import ChatRepository
from app.chat.service import ChatService
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.file_search.dependencies import get_file_search_service
from app.file_search.service import FileSearchService


def get_chat_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> ChatRepository:
    return ChatRepository(session)


def get_ai_provider(settings: Annotated[Settings, Depends(get_settings)]) -> AIProvider:
    return GeminiProvider(settings)


def get_chat_service(
    repository: Annotated[ChatRepository, Depends(get_chat_repository)],
    ai_provider: Annotated[AIProvider, Depends(get_ai_provider)],
    file_search_service: Annotated[FileSearchService, Depends(get_file_search_service)],
) -> ChatService:
    return ChatService(repository, ai_provider, file_search_service)
