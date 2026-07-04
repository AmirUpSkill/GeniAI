from datetime import UTC, datetime
from typing import cast

import pytest

from app.auth.google_oauth import GoogleUserInfo
from app.auth.repository import AuthRepository
from app.auth.service import AuthService, GoogleOAuthClientProtocol
from app.core.config import Settings
from app.core.errors import AuthProviderError, AuthUnauthorizedError
from app.core.security import hash_session_token
from app.models.auth_session import AuthSession
from app.models.user import User


class FakeSession:
    def __init__(self) -> None:
        self.committed = False

    async def commit(self) -> None:
        self.committed = True


class FakeRepository:
    def __init__(self, existing_user: User | None = None) -> None:
        self.session = FakeSession()
        self.existing_user = existing_user
        self.created_user: User | None = None
        self.created_session: AuthSession | None = None
        self.deleted_hash: str | None = None

    async def get_user_by_provider_user_id(self, provider_user_id: str) -> User | None:
        _ = provider_user_id
        return self.existing_user

    async def create_user_from_google(self, google_user: GoogleUserInfo) -> User:
        self.created_user = User(
            id="usr_new",
            email=google_user.email,
            full_name=google_user.full_name,
            avatar_url=google_user.avatar_url,
            provider="google",
            provider_user_id=google_user.provider_user_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return self.created_user

    async def create_session(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
    ) -> AuthSession:
        self.created_session = AuthSession(
            id="ses_test",
            user_id=user_id,
            session_token_hash=token_hash,
            expires_at=expires_at,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        return self.created_session

    async def get_user_by_session_hash(self, token_hash: str, now: datetime) -> User | None:
        _ = (token_hash, now)
        return self.existing_user

    async def delete_session_by_hash(self, token_hash: str) -> None:
        self.deleted_hash = token_hash


class FakeGoogleClient:
    def __init__(self, google_user: GoogleUserInfo) -> None:
        self.google_user = google_user

    async def exchange_code_for_user(self, code: str) -> GoogleUserInfo:
        _ = code
        return self.google_user


def build_service(
    repository: FakeRepository,
    google_user: GoogleUserInfo,
    settings: Settings | None = None,
) -> AuthService:
    return AuthService(
        cast(AuthRepository, repository),
        cast(GoogleOAuthClientProtocol, FakeGoogleClient(google_user)),
        settings or Settings(SESSION_SECRET_KEY="test-secret", _env_file=None),
    )


def build_google_user(email_verified: bool = True) -> GoogleUserInfo:
    return GoogleUserInfo(
        provider_user_id="google_123",
        email="amir@example.com",
        email_verified=email_verified,
        full_name="Amir Abdallah",
        avatar_url="https://example.com/avatar.png",
    )


@pytest.mark.asyncio
async def test_google_callback_creates_new_user_and_hashed_session() -> None:
    repository = FakeRepository()
    service = build_service(repository, build_google_user())

    user, raw_token = await service.authenticate_google_callback("valid-code")

    assert user.id == "usr_new"
    assert repository.created_user is not None
    assert repository.created_session is not None
    assert repository.created_session.session_token_hash != raw_token
    assert repository.created_session.session_token_hash == hash_session_token(
        raw_token,
        "test-secret",
    )
    assert repository.session.committed is True


@pytest.mark.asyncio
async def test_google_callback_reuses_existing_user() -> None:
    existing_user = User(
        id="usr_existing",
        email="amir@example.com",
        full_name="Amir Abdallah",
        avatar_url=None,
        provider="google",
        provider_user_id="google_123",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    repository = FakeRepository(existing_user=existing_user)
    service = build_service(repository, build_google_user())

    user, _raw_token = await service.authenticate_google_callback("valid-code")

    assert user is existing_user
    assert repository.created_user is None
    assert repository.created_session is not None


@pytest.mark.asyncio
async def test_google_callback_rejects_unverified_email() -> None:
    repository = FakeRepository()
    service = build_service(repository, build_google_user(email_verified=False))

    with pytest.raises(AuthProviderError):
        await service.authenticate_google_callback("valid-code")


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_session_token() -> None:
    service = build_service(FakeRepository(), build_google_user())

    with pytest.raises(AuthUnauthorizedError):
        await service.get_current_user_from_token(None)


@pytest.mark.asyncio
async def test_logout_deletes_hashed_session_token() -> None:
    repository = FakeRepository()
    service = build_service(repository, build_google_user())

    await service.logout("raw-token")

    assert repository.deleted_hash == hash_session_token("raw-token", "test-secret")
    assert repository.session.committed is True
