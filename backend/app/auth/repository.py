from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.google_oauth import GoogleUserInfo
from app.models.auth_session import AuthSession
from app.models.user import User


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_provider_user_id(self, provider_user_id: str) -> User | None:
        result = await self.session.execute(
            select(User).where(
                User.provider == "google",
                User.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_user_from_google(self, google_user: GoogleUserInfo) -> User:
        user = User(
            email=google_user.email,
            full_name=google_user.full_name,
            avatar_url=google_user.avatar_url,
            provider="google",
            provider_user_id=google_user.provider_user_id,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def create_session(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> AuthSession:
        auth_session = AuthSession(
            user_id=user_id,
            session_token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(auth_session)
        await self.session.flush()
        await self.session.refresh(auth_session)
        return auth_session

    async def get_user_by_session_hash(self, token_hash: str, now: datetime) -> User | None:
        result = await self.session.execute(
            select(User)
            .join(AuthSession, AuthSession.user_id == User.id)
            .where(
                AuthSession.session_token_hash == token_hash,
                AuthSession.expires_at > now,
            )
        )
        return result.scalar_one_or_none()

    async def delete_session_by_hash(self, token_hash: str) -> None:
        await self.session.execute(
            delete(AuthSession).where(AuthSession.session_token_hash == token_hash)
        )
