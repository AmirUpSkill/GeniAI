from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ErrorBody(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorBody


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    email: str
    full_name: str = Field(serialization_alias="fullName")
    avatar_url: str | None = Field(default=None, serialization_alias="avatarUrl")
    provider: str
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class AuthenticatedUserResponse(BaseModel):
    success: bool = True
    data: AuthenticatedUser


class LogoutResponse(BaseModel):
    success: bool = True
    message: str
