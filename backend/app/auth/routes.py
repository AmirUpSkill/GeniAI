import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app.auth.dependencies import get_auth_service, get_current_user, get_google_oauth_client
from app.auth.google_oauth import GoogleOAuthClient
from app.auth.schemas import AuthenticatedUser, AuthenticatedUserResponse, LogoutResponse
from app.auth.service import AuthService
from app.core.config import Settings, get_settings
from app.core.cookies import clear_session_cookie, set_session_cookie
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
async def google_login(
    google_client: Annotated[GoogleOAuthClient, Depends(get_google_oauth_client)],
    redirect_uri: Annotated[str | None, Query(alias="redirectUri")] = None,
) -> RedirectResponse:
    state = redirect_uri or secrets.token_urlsafe(24)
    url = google_client.build_authorization_url(state=state)
    return RedirectResponse(url=url, status_code=302)


@router.get("/google/callback")
async def google_callback(
    code: str,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    state: str | None = None,
) -> RedirectResponse:
    _ = state
    _user, raw_token = await auth_service.authenticate_google_callback(code)
    redirect = RedirectResponse(url=f"{settings.frontend_url}/chat", status_code=302)
    set_session_cookie(redirect, raw_token, settings)
    return redirect


@router.get("/me", response_model=AuthenticatedUserResponse)
async def auth_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(data=AuthenticatedUser.model_validate(current_user))


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    raw_token = request.cookies.get(settings.session_cookie_name)
    await auth_service.logout(raw_token)
    response = LogoutResponse(message="User logged out successfully.")
    json_response = JSONResponse(content=response.model_dump(mode="json"))
    clear_session_cookie(json_response, settings)
    return json_response
