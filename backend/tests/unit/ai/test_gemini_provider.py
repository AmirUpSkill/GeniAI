from datetime import UTC, datetime

from app.ai.gemini_provider import build_prompt
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
