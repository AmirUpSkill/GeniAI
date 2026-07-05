from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MessageRole = Literal["user", "assistant", "system"]


class ChatSessionCreate(BaseModel):
    title: str = Field(default="New chat", min_length=1, max_length=160)


class ChatSessionUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=160)


class ChatSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    title: str
    summary: str | None = None
    created_at: datetime = Field(serialization_alias="createdAt")
    updated_at: datetime = Field(serialization_alias="updatedAt")


class ChatSessionResponse(BaseModel):
    success: bool = True
    data: ChatSessionRead


class ChatSessionListResponse(BaseModel):
    success: bool = True
    data: list[ChatSessionRead]


class ChatMessageCreate(BaseModel):
    role: MessageRole = "user"
    content: str = Field(min_length=1)


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str
    chat_session_id: str = Field(serialization_alias="chatSessionId")
    role: MessageRole
    content: str
    created_at: datetime = Field(serialization_alias="createdAt")


class ChatMessageResponse(BaseModel):
    success: bool = True
    data: ChatMessageRead


class ChatMessageListResponse(BaseModel):
    success: bool = True
    data: list[ChatMessageRead]


class ChatTurnCreate(BaseModel):
    content: str = Field(min_length=1)


class ChatTurnData(BaseModel):
    user_message: ChatMessageRead = Field(serialization_alias="userMessage")
    assistant_message: ChatMessageRead = Field(serialization_alias="assistantMessage")


class ChatTurnResponse(BaseModel):
    success: bool = True
    data: ChatTurnData


class ChatDeleteResponse(BaseModel):
    success: bool = True
    message: str
