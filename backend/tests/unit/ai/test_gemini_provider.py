from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.ai.gemini_provider import GeminiProvider, build_prompt
from app.core.config import Settings
from app.core.errors import AIProviderError
from app.models.chat_message import ChatMessage


def test_build_prompt_includes_recent_conversation_roles() -> None:
    prompt = build_prompt(
        [
            ChatMessage(
                id="msg_1",
                chat_session_id="chat_1",
                role="user",
                content="Hello",
                created_at=datetime.now(UTC),
            ),
            ChatMessage(
                id="msg_2",
                chat_session_id="chat_1",
                role="assistant",
                content="Hi there",
                created_at=datetime.now(UTC),
            ),
        ]
    )

    assert "USER: Hello" in prompt
    assert "ASSISTANT: Hi there" in prompt
    assert prompt.endswith("ASSISTANT:")


class FakeAsyncStream:
    def __init__(self, events: list[object]) -> None:
        self.events = events

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.events:
            raise StopAsyncIteration
        return self.events.pop(0)


class FakeInteractions:
    def __init__(self, events: list[object]) -> None:
        self.events = events
        self.kwargs: dict[str, Any] = {}

    async def create(self, **kwargs: Any) -> FakeAsyncStream:
        self.kwargs = kwargs
        return FakeAsyncStream(self.events.copy())


class FakeAio:
    def __init__(self, events: list[object]) -> None:
        self.interactions = FakeInteractions(events)
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakeClient:
    def __init__(self, events: list[object]) -> None:
        self.aio = FakeAio(events)


def event(event_type: str, **values: Any) -> object:
    return SimpleNamespace(event_type=event_type, **values)


def build_message() -> ChatMessage:
    return ChatMessage(
        id="msg_1",
        chat_session_id="chat_1",
        role="user",
        content="Hello",
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_stream_reply_yields_only_model_output_text(monkeypatch: pytest.MonkeyPatch) -> None:
    events = [
        event("step.start", index=0, step=SimpleNamespace(type="thought")),
        event(
            "step.delta",
            index=0,
            delta=SimpleNamespace(type="thought_summary", text="hidden"),
        ),
        event("step.stop", index=0),
        event("future.event"),
        event("step.start", index=1, step=SimpleNamespace(type="model_output")),
        event("step.delta", index=1, delta=SimpleNamespace(type="text", text="Hello ")),
        event("step.delta", index=1, delta=SimpleNamespace(type="text", text="Amir")),
        event("step.stop", index=1),
        event("interaction.completed"),
    ]
    client = FakeClient(events)
    monkeypatch.setattr("app.ai.gemini_provider.genai.Client", lambda **_: client)
    provider = GeminiProvider(Settings(GEMINI_API_KEY="test-key"))

    chunks = [chunk async for chunk in provider.stream_reply([build_message()])]

    assert [chunk.text for chunk in chunks] == ["Hello ", "Amir"]
    assert client.aio.interactions.kwargs["stream"] is True
    assert client.aio.closed is True


@pytest.mark.asyncio
async def test_generate_reply_collects_and_deduplicates_file_citations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    citation = SimpleNamespace(
        type="file_citation",
        file_name="guide.pdf",
        page_number=3,
        source="A useful passage",
        media_id=None,
        custom_metadata={"section": "intro"},
    )
    events = [
        event("step.start", index=0, step=SimpleNamespace(type="file_search_call")),
        event("step.stop", index=0),
        event("step.start", index=1, step=SimpleNamespace(type="model_output")),
        event("step.delta", index=1, delta=SimpleNamespace(type="text", text="Grounded")),
        event(
            "step.delta",
            index=1,
            delta=SimpleNamespace(
                type="text_annotation_delta",
                annotations=[citation, citation],
            ),
        ),
        event("step.stop", index=1),
        event("interaction.completed"),
    ]
    client = FakeClient(events)
    monkeypatch.setattr("app.ai.gemini_provider.genai.Client", lambda **_: client)
    provider = GeminiProvider(Settings(GEMINI_API_KEY="test-key"))

    reply = await provider.generate_reply([build_message()], "fileSearchStores/store-1")

    assert reply.text == "Grounded"
    assert len(reply.citations) == 1
    assert reply.citations[0].page_number == 3
    assert client.aio.interactions.kwargs["tools"][0]["type"] == "file_search"


@pytest.mark.asyncio
async def test_generate_reply_rejects_empty_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeClient([event("interaction.completed")])
    monkeypatch.setattr("app.ai.gemini_provider.genai.Client", lambda **_: client)
    provider = GeminiProvider(Settings(GEMINI_API_KEY="test-key"))

    with pytest.raises(AIProviderError):
        await provider.generate_reply([build_message()])
