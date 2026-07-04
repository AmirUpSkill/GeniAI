from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import Settings
from app.core.errors import AuthProviderError


@dataclass(frozen=True)
class GoogleUserInfo:
    provider_user_id: str
    email: str
    email_verified: bool
    full_name: str
    avatar_url: str | None


class GoogleOAuthClient:
    authorization_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def build_authorization_url(self, redirect_uri: str | None = None, state: str | None = None) -> str:
        query = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": redirect_uri or self.settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        if state is not None:
            query["state"] = state

        return f"{self.authorization_url}?{urlencode(query)}"

    async def exchange_code_for_user(self, code: str) -> GoogleUserInfo:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_response = await client.post(
                self.token_url,
                data={
                    "code": code,
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "redirect_uri": self.settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_response.status_code >= 400:
                raise AuthProviderError()

            token_payload = token_response.json()
            access_token = self._read_required_string(token_payload, "access_token")

            userinfo_response = await client.get(
                self.userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if userinfo_response.status_code >= 400:
                raise AuthProviderError()

            payload = userinfo_response.json()

        return GoogleUserInfo(
            provider_user_id=self._read_required_string(payload, "sub"),
            email=self._read_required_string(payload, "email"),
            email_verified=self._read_bool(payload, "email_verified"),
            full_name=self._read_required_string(payload, "name"),
            avatar_url=self._read_optional_string(payload, "picture"),
        )

    def _read_required_string(self, payload: dict[str, Any], key: str) -> str:
        value = payload.get(key)
        if not isinstance(value, str) or value == "":
            raise AuthProviderError()
        return value

    def _read_optional_string(self, payload: dict[str, Any], key: str) -> str | None:
        value = payload.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise AuthProviderError()
        return value

    def _read_bool(self, payload: dict[str, Any], key: str) -> bool:
        value = payload.get(key)
        if not isinstance(value, bool):
            raise AuthProviderError()
        return value
