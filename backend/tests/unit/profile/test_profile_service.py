from datetime import UTC, datetime

from app.models.user import User
from app.profile.service import ProfileService


def test_profile_service_returns_safe_profile_shape() -> None:
    user = User(
        id="usr_123",
        email="amir@example.com",
        full_name="Amir Abdallah",
        avatar_url="https://example.com/avatar.png",
        provider="google",
        provider_user_id="google_secret",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    profile = ProfileService().get_profile(user)
    payload = profile.model_dump(by_alias=True)

    assert payload["email"] == "amir@example.com"
    assert payload["fullName"] == "Amir Abdallah"
    assert "providerUserId" not in payload
    assert "sessionTokenHash" not in payload
