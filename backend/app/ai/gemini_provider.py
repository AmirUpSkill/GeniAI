from typing import Any, cast

from google import genai

from app.core.config import Settings
from app.core.errors import AIProviderError
from app.models.chat_message import ChatMessage


class GeminiProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_reply(self, messages: list[ChatMessage]) -> str:
        if self.settings.gemini_api_key.strip() == "":
            raise AIProviderError("Gemini API key is not configured.")

        try:
            client = genai.Client(api_key=self.settings.gemini_api_key)
            response = await client.aio.models.generate_content(
                model=self.settings.gemini_model,
                contents=build_prompt(messages),
            )
        except Exception as exc:
            raise AIProviderError() from exc

        text = cast(str | None, getattr(cast(Any, response), "text", None))
        if text is None or text.strip() == "":
            raise AIProviderError("AI provider returned an empty response.")

        return text.strip()


def build_prompt(messages: list[ChatMessage]) -> str:
    transcript = "\n".join(
        f"{message.role.upper()}: {message.content}" for message in messages[-24:]
    )
    return (
        "You are Geni, a concise and useful AI assistant inside a SaaS chat app. "
        "Answer the user's latest message using the conversation context.\n\n"
        f"{transcript}\n\nASSISTANT:"
    )
