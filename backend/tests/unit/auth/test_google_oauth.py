from urllib.parse import parse_qs, urlparse

from app.auth.google_oauth import GoogleOAuthClient
from app.core.config import Settings


def test_google_oauth_client_builds_authorization_url() -> None:
    settings = Settings(
        GOOGLE_CLIENT_ID="client-id",
        GOOGLE_REDIRECT_URI="http://localhost:8000/api/auth/google/callback",
        _env_file=None,
    )
    client = GoogleOAuthClient(settings)

    url = client.build_authorization_url(state="state-token")
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "accounts.google.com"
    assert query["client_id"] == ["client-id"]
    assert query["redirect_uri"] == ["http://localhost:8000/api/auth/google/callback"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["openid email profile"]
    assert query["state"] == ["state-token"]
