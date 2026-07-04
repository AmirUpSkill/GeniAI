from typing import Annotated

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.models.user import User
from app.profile.schemas import ProfileResponse
from app.profile.service import ProfileService

router = APIRouter(prefix="/profile", tags=["profile"])


def get_profile_service() -> ProfileService:
    return ProfileService()


@router.get("/me", response_model=ProfileResponse)
async def profile_me(
    current_user: Annotated[User, Depends(get_current_user)],
    profile_service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    return ProfileResponse(data=profile_service.get_profile(current_user))
