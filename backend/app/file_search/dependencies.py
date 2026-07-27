from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.file_search.gemini import GeminiFileSearchGateway
from app.file_search.repository import FileSearchRepository
from app.file_search.service import FileSearchService


def get_file_search_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FileSearchRepository:
    return FileSearchRepository(session)


def get_file_search_gateway(
    settings: Annotated[Settings, Depends(get_settings)],
) -> GeminiFileSearchGateway:
    return GeminiFileSearchGateway(settings)


def get_file_search_service(
    repository: Annotated[FileSearchRepository, Depends(get_file_search_repository)],
    gateway: Annotated[GeminiFileSearchGateway, Depends(get_file_search_gateway)],
) -> FileSearchService:
    return FileSearchService(repository, gateway)

