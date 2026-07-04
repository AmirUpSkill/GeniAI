from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.google_oauth import GoogleOAuthClient
from app.auth.repository import AuthRepository
from app.auth.service import AuthService
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.user import User


def get_google_oauth_client(settings: Annotated[Settings, Depends(get_settings)]) -> GoogleOAuthClient:
    return GoogleOAuthClient(settings)


def get_auth_repository(session: Annotated[AsyncSession, Depends(get_db_session)]) -> AuthRepository:
    return AuthRepository(session)


def get_auth_service(
    repository: Annotated[AuthRepository, Depends(get_auth_repository)],
    google_client: Annotated[GoogleOAuthClient, Depends(get_google_oauth_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(repository, google_client, settings)


async def get_current_user(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    raw_token = request.cookies.get(settings.session_cookie_name)
    return await auth_service.get_current_user_from_token(raw_token)
