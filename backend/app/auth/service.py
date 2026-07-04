from datetime import UTC, datetime, timedelta
from typing import Protocol

from app.auth.google_oauth import GoogleUserInfo
from app.auth.repository import AuthRepository
from app.core.config import Settings
from app.core.errors import AuthProviderError, AuthUnauthorizedError
from app.core.security import generate_session_token, hash_session_token
from app.models.user import User


class GoogleOAuthClientProtocol(Protocol):
    async def exchange_code_for_user(self, code: str) -> GoogleUserInfo: ...


class AuthService:
    def __init__(
        self,
        repository: AuthRepository,
        google_client: GoogleOAuthClientProtocol,
        settings: Settings,
    ) -> None:
        self.repository = repository
        self.google_client = google_client
        self.settings = settings

    async def authenticate_google_callback(self, code: str) -> tuple[User, str]:
        google_user = await self.google_client.exchange_code_for_user(code)
        if not google_user.email_verified:
            raise AuthProviderError("Google email is not verified.", code="AUTH_EMAIL_NOT_VERIFIED")

        user = await self.repository.get_user_by_provider_user_id(google_user.provider_user_id)
        if user is None:
            user = await self.repository.create_user_from_google(google_user)

        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token, self.settings.session_secret_key)
        expires_at = datetime.now(UTC) + timedelta(days=self.settings.session_ttl_days)
        await self.repository.create_session(user.id, token_hash, expires_at)
        await self.repository.session.commit()
        return user, raw_token

    async def get_current_user_from_token(self, raw_token: str | None) -> User:
        if raw_token is None or raw_token == "":
            raise AuthUnauthorizedError()

        token_hash = hash_session_token(raw_token, self.settings.session_secret_key)
        user = await self.repository.get_user_by_session_hash(token_hash, datetime.now(UTC))
        if user is None:
            raise AuthUnauthorizedError()
        return user

    async def logout(self, raw_token: str | None) -> None:
        if raw_token is None or raw_token == "":
            return

        token_hash = hash_session_token(raw_token, self.settings.session_secret_key)
        await self.repository.delete_session_by_hash(token_hash)
        await self.repository.session.commit()
