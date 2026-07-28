from dataclasses import dataclass, field
from collections.abc import AsyncIterator
from typing import Any, Protocol

from app.models.chat_message import ChatMessage


@dataclass(frozen=True)
class FileCitation:
    """
        Provider-neutral citation data saved alongside an assistant message.
    """
    file_name: str | None
    source_excerpt: str
    page_number: int | None = None
    media_id: str | None = None
    custom_metadata: dict[str, Any] | None = None


@dataclass(frozen=True)
class AIReply:
    """
        A generated answer and the evidence used to produce it.
    """
    text: str
    citations: list[FileCitation] = field(default_factory=list)


@dataclass(frozen=True)
class AIStreamChunk:
    """
        Provider-neutral incremental output from an AI generation.
    """
    text: str = ""
    citations: list[FileCitation] = field(default_factory=list)


class AIProvider(Protocol):
    async def generate_reply(
        self,
        messages: list[ChatMessage],
        file_search_store_name: str | None = None,
    ) -> AIReply: ...

    def stream_reply(
        self,
        messages: list[ChatMessage],
        file_search_store_name: str | None = None,
    ) -> AsyncIterator[AIStreamChunk]: ...
