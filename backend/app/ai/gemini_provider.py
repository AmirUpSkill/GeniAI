from typing import Any, cast

from google import genai

from app.ai.provider import AIReply, FileCitation
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
        if self.settings.gemini_api_key.strip() == "":
            raise AIProviderError("Gemini API key is not configured.")

        try:
            client = genai.Client(api_key=self.settings.gemini_api_key)
            if file_search_store_name is not None:
                return await self._generate_file_search_reply(
                    client,
                    messages,
                    file_search_store_name,
                )

            response = await client.aio.models.generate_content(
                model=self.settings.gemini_model,
                contents=build_prompt(messages),
            )
        except Exception as exc:
            raise AIProviderError() from exc

        text = cast(str | None, getattr(cast(Any, response), "text", None))
        if text is None or text.strip() == "":
            raise AIProviderError("AI provider returned an empty response.")

        return AIReply(text=text.strip())

    async def _generate_file_search_reply(
        self,
        client: genai.Client,
        messages: list[ChatMessage],
        store_name: str,
    ) -> AIReply:
        """
            Generate a document-grounded answer and normalize its annotations.
        """

        interaction = cast(
            Any,
            await client.aio.interactions.create(
                model=self.settings.file_search_generation_model,
                input=build_file_search_prompt(messages),
                system_instruction=(
                    "You are Geni, a concise document assistant. Answer from the "
                    "indexed document. If the document does not contain the answer, "
                    "say that clearly instead of guessing. Preserve important numbers "
                    "and qualifications from the source."
                ),
                tools=[
                    {
                        "type": "file_search",
                        "file_search_store_names": [store_name],
                    }
                ],
            ),
        )
        answer_parts: list[str] = []
        citations: list[FileCitation] = []
        citation_keys: set[tuple[str | None, int | None, str]] = set()

        for step in interaction.steps or []:
            if getattr(step, "type", None) != "model_output":
                continue
            for block in getattr(step, "content", None) or []:
                if getattr(block, "type", None) != "text":
                    continue
                block_text = cast(str | None, getattr(block, "text", None))
                if block_text:
                    answer_parts.append(block_text)

                for annotation in getattr(block, "annotations", None) or []:
                    if getattr(annotation, "type", None) != "file_citation":
                        continue
                    source = cast(str | None, getattr(annotation, "source", None))
                    if not source:
                        continue
                    file_name = cast(str | None, getattr(annotation, "file_name", None))
                    page_number = cast(int | None, getattr(annotation, "page_number", None))
                    key = (file_name, page_number, " ".join(source.split()))
                    if key in citation_keys:
                        continue
                    citation_keys.add(key)
                    citations.append(
                        FileCitation(
                            file_name=file_name,
                            source_excerpt=source.strip(),
                            page_number=page_number,
                            media_id=cast(
                                str | None,
                                getattr(annotation, "media_id", None),
                            ),
                            custom_metadata=cast(
                                dict[str, Any] | None,
                                getattr(annotation, "custom_metadata", None),
                            ),
                        )
                    )

        text = "\n".join(answer_parts).strip()
        if not text:
            text = (interaction.output_text or "").strip()
        if not text:
            raise AIProviderError("AI provider returned an empty File Search response.")
        return AIReply(text=text, citations=citations)


def build_prompt(messages: list[ChatMessage]) -> str:
    transcript = "\n".join(
        f"{message.role.upper()}: {message.content}" for message in messages[-24:]
    )
    return (
        "You are Geni, a concise and useful AI assistant inside a SaaS chat app. "
        "Answer the user's latest message using the conversation context.\n\n"
        f"{transcript}\n\nASSISTANT:"
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
        f"{transcript}\n\nASSISTANT:"
    )
