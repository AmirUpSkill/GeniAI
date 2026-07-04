from app.auth.schemas import AuthenticatedUser
from app.models.user import User


class ProfileService:
    def get_profile(self, user: User) -> AuthenticatedUser:
        return AuthenticatedUser.model_validate(user)
