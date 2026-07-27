from collections.abc import AsyncIterator
from typing import Any, cast

from google import genai

from app.ai.provider import AIReply, AIStreamChunk, FileCitation
from app.core.config import Settings
from app.core.errors import AIProviderError
from app.models.chat_message import ChatMessage


class GeminiProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_reply(
        self,
        messages: list[ChatMessage],
        file_search_store_name: str | None = None,
    ) -> AIReply:
        answer_parts: list[str] = []
        citations: list[FileCitation] = []
        citation_keys: set[tuple[str | None, int | None, str]] = set()
        async for chunk in self.stream_reply(messages, file_search_store_name):
            if chunk.text:
                answer_parts.append(chunk.text)
            for citation in chunk.citations:
                key = citation_key(citation)
                if key not in citation_keys:
                    citation_keys.add(key)
                    citations.append(citation)

        text = "".join(answer_parts).strip()
        if not text:
            raise AIProviderError("AI provider returned an empty response.")
        return AIReply(text=text, citations=citations)

    async def stream_reply(
        self,
        messages: list[ChatMessage],
        file_search_store_name: str | None = None,
    ) -> AsyncIterator[AIStreamChunk]:
        if self.settings.gemini_api_key.strip() == "":
            raise AIProviderError("Gemini API key is not configured.")

        client = genai.Client(api_key=self.settings.gemini_api_key)
        active_steps: dict[int, str] = {}
        try:
            stream = cast(
                Any,
                await client.aio.interactions.create(
                    model=(
                        self.settings.file_search_generation_model
                        if file_search_store_name is not None
                        else self.settings.gemini_model
                    ),
                    input=(
                        build_file_search_prompt(messages)
                        if file_search_store_name is not None
                        else build_prompt(messages)
                    ),
                    system_instruction=(
                        "You are Geni, a concise document assistant. Answer from the "
                        "indexed document. If the document does not contain the answer, "
                        "say that clearly instead of guessing. Preserve important numbers "
                        "and qualifications from the source."
                        if file_search_store_name is not None
                        else (
                            "You are Geni, a concise and useful AI assistant inside a "
                            "SaaS chat app. Answer the user's latest message using the "
                            "conversation context."
                        )
                    ),
                    stream=True,
                    **(
                        {
                            "tools": [
                                {
                                    "type": "file_search",
                                    "file_search_store_names": [file_search_store_name],
                                }
                            ]
                        }
                        if file_search_store_name is not None
                        else {}
                    ),
                ),
            )
            async for event in stream:
                event_type = getattr(event, "event_type", None)
                index = cast(int | None, getattr(event, "index", None))
                if event_type == "step.start" and index is not None:
                    active_steps[index] = cast(
                        str,
                        getattr(getattr(event, "step", None), "type", ""),
                    )
                    continue
                if event_type == "step.stop" and index is not None:
                    active_steps.pop(index, None)
                    continue
                if event_type == "error":
                    error = getattr(event, "error", None)
                    message = cast(str | None, getattr(error, "message", None))
                    raise AIProviderError(message or "Gemini streaming request failed.")
                if (
                    event_type != "step.delta"
                    or index is None
                    or active_steps.get(index) != "model_output"
                ):
                    continue

                delta = getattr(event, "delta", None)
                delta_type = getattr(delta, "type", None)
                if delta_type == "text":
                    text = cast(str | None, getattr(delta, "text", None))
                    if text:
                        yield AIStreamChunk(text=text)
                elif delta_type == "text_annotation_delta":
                    citations = normalize_citations(
                        cast(list[Any], getattr(delta, "annotations", None) or [])
                    )
                    if citations:
                        yield AIStreamChunk(citations=citations)
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError() from exc
        finally:
            await client.aio.aclose()


def normalize_citations(annotations: list[Any]) -> list[FileCitation]:
    citations: list[FileCitation] = []
    citation_keys: set[tuple[str | None, int | None, str]] = set()
    for annotation in annotations:
        if getattr(annotation, "type", None) != "file_citation":
            continue
        source = cast(str | None, getattr(annotation, "source", None))
        if not source:
            continue
        citation = FileCitation(
            file_name=cast(str | None, getattr(annotation, "file_name", None)),
            source_excerpt=source.strip(),
            page_number=cast(int | None, getattr(annotation, "page_number", None)),
            media_id=cast(str | None, getattr(annotation, "media_id", None)),
            custom_metadata=cast(
                dict[str, Any] | None,
                getattr(annotation, "custom_metadata", None),
            ),
        )
        key = citation_key(citation)
        if key not in citation_keys:
            citation_keys.add(key)
            citations.append(citation)
    return citations


def citation_key(citation: FileCitation) -> tuple[str | None, int | None, str]:
    return (
        citation.file_name,
        citation.page_number,
        " ".join(citation.source_excerpt.split()),
    )


def build_prompt(messages: list[ChatMessage]) -> str:
    transcript = "\n".join(
        f"{message.role.upper()}: {message.content}" for message in messages[-24:]
    )
    return (
        "The following transcript contains recent conversation context. Respond to "
        "the latest user message.\n\n"
        f"{transcript}"
    )


def build_file_search_prompt(messages: list[ChatMessage]) -> str:
    """
        Keep recent conversation context while making the latest question explicit.
    """

    recent_messages = messages[-24:]
    transcript = "\n".join(
        f"{message.role.upper()}: {message.content}" for message in recent_messages
    )
    return (
        "Use File Search to answer the latest user message from the indexed "
        "document. The preceding messages are conversation context only.\n\n"
        f"{transcript}"
    )
