from typing import Protocol

from app.models.chat_message import ChatMessage


class AIProvider(Protocol):
    async def generate_reply(self, messages: list[ChatMessage]) -> str: ...
