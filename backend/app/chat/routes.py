from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_current_user
from app.chat.dependencies import get_chat_service
from app.chat.schemas import (
    ChatDeleteResponse,
    ChatMessageCreate,
    ChatMessageListResponse,
    ChatMessageRead,
    ChatMessageResponse,
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionRead,
    ChatSessionResponse,
    ChatSessionUpdate,
    ChatTurnCreate,
    ChatTurnData,
    ChatTurnResponse,
)
from app.chat.service import ChatService
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_session(
    payload: ChatSessionCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatSessionResponse:
    chat_session = await chat_service.create_session(current_user, payload)
    return ChatSessionResponse(data=ChatSessionRead.model_validate(chat_session))


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatSessionListResponse:
    chat_sessions = await chat_service.list_sessions(current_user)
    return ChatSessionListResponse(
        data=[ChatSessionRead.model_validate(chat_session) for chat_session in chat_sessions]
    )


@router.get("/sessions/{chat_session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    chat_session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatSessionResponse:
    chat_session = await chat_service.get_session(current_user, chat_session_id)
    return ChatSessionResponse(data=ChatSessionRead.model_validate(chat_session))


@router.patch("/sessions/{chat_session_id}", response_model=ChatSessionResponse)
async def update_chat_session(
    chat_session_id: str,
    payload: ChatSessionUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatSessionResponse:
    chat_session = await chat_service.update_session(current_user, chat_session_id, payload)
    return ChatSessionResponse(data=ChatSessionRead.model_validate(chat_session))


@router.delete("/sessions/{chat_session_id}", response_model=ChatDeleteResponse)
async def delete_chat_session(
    chat_session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatDeleteResponse:
    await chat_service.delete_session(current_user, chat_session_id)
    return ChatDeleteResponse(message="Chat session deleted successfully.")


@router.post(
    "/sessions/{chat_session_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_message(
    chat_session_id: str,
    payload: ChatMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatMessageResponse:
    message = await chat_service.create_message(current_user, chat_session_id, payload)
    return ChatMessageResponse(data=ChatMessageRead.model_validate(message))


@router.get(
    "/sessions/{chat_session_id}/messages",
    response_model=ChatMessageListResponse,
)
async def list_chat_messages(
    chat_session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatMessageListResponse:
    messages = await chat_service.list_messages(current_user, chat_session_id)
    return ChatMessageListResponse(
        data=[ChatMessageRead.model_validate(message) for message in messages]
    )


@router.post(
    "/sessions/{chat_session_id}/turns",
    response_model=ChatTurnResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_turn(
    chat_session_id: str,
    payload: ChatTurnCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatTurnResponse:
    user_message, assistant_message = await chat_service.create_ai_turn(
        current_user,
        chat_session_id,
        payload,
    )
    return ChatTurnResponse(
        data=ChatTurnData(
            user_message=ChatMessageRead.model_validate(user_message),
            assistant_message=ChatMessageRead.model_validate(assistant_message),
        )
    )
