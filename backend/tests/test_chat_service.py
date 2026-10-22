
from unittest.mock import Mock

import pytest

from app.ai.service import AIServiceError
from app.services import chat_service as chat_module
from app.services.chat_service import ChatService


def test_ai_failure_does_not_save_chat_messages(monkeypatch: pytest.MonkeyPatch):
    """AI failure must occur before either chat message is saved."""

    # Mock the database session and existing conversation.
    db = Mock()

    monkeypatch.setattr(
        chat_module,
        "get_conversation",
        Mock(return_value=Mock()),
    )

    monkeypatch.setattr(
        chat_module,
        "get_conversation_messages",
        Mock(return_value=[]),
    )

    # Prevent real memory processing or database changes.
    monkeypatch.setattr(
        chat_module,
        "is_memory_question",
        Mock(return_value=False),
    )

    monkeypatch.setattr(
        chat_module,
        "process_memory",
        Mock(return_value=None),
    )

    # Prevent a real Gemini API call.
    service = ChatService()

    monkeypatch.setattr(
        service.ai_service,
        "generate_response",
        Mock(
            side_effect=AIServiceError(
                "Controlled test failure",
                status_code=503,
            )
        ),
    )

    # Monitor attempts to save chat messages.
    add_message_mock = Mock()

    monkeypatch.setattr(
        chat_module,
        "add_message",
        add_message_mock,
    )

    # Verify that AI failure prevents message persistence.
    with pytest.raises(AIServiceError) as error:
        service.chat(
            db=db,
            conversation_id=13,
            user_id=2,
            message="Explain quantum computing.",
        )

    assert error.value.status_code == 503
    add_message_mock.assert_not_called()
    db.commit.assert_not_called()


def test_successful_chat_saves_both_messages(monkeypatch: pytest.MonkeyPatch):
    """Successful AI generation saves both messages in one transaction."""

    db = Mock()
    conversation = Mock()

    # Mock the user message.
    user_message = Mock()
    user_message.id = 101
    user_message.role = "user"
    user_message.content = "Hello!"

    # Mock the assistant message.
    assistant_message = Mock()
    assistant_message.id = 102
    assistant_message.role = "assistant"
    assistant_message.content = "Hello! How can I help?"

    # Mock conversation lookup and history.
    monkeypatch.setattr(
        chat_module,
        "get_conversation",
        Mock(return_value=conversation),
    )

    monkeypatch.setattr(
        chat_module,
        "get_conversation_messages",
        Mock(return_value=[]),
    )

    # Disable real memory processing during this test.
    monkeypatch.setattr(
        chat_module,
        "is_memory_question",
        Mock(return_value=False),
    )

    monkeypatch.setattr(
        chat_module,
        "process_memory",
        Mock(return_value=None),
    )

    # Return both mocked messages from the persistence function.
    add_message_mock = Mock(
        side_effect=[
            user_message,
            assistant_message,
        ]
    )

    monkeypatch.setattr(
        chat_module,
        "add_message",
        add_message_mock,
    )

    # Mock AI generation to avoid calling Gemini.
    service = ChatService()

    monkeypatch.setattr(
        service.ai_service,
        "generate_response",
        Mock(
            return_value="Hello! How can I help?"
        ),
    )

    # Execute the chat service.
    result = service.chat(
        db=db,
        conversation_id=13,
        user_id=2,
        message="Hello!",
    )

    # Verify the returned result.
    assert result["conversation_id"] == 13
    assert result["user_message"] is user_message
    assert result["assistant_message"] is assistant_message

    # Verify that both messages were added correctly.
    assert add_message_mock.call_count == 2

    assert add_message_mock.call_args_list[0].args[2:] == (
        "user",
        "Hello!",
    )

    assert add_message_mock.call_args_list[1].args[2:] == (
        "assistant",
        "Hello! How can I help?",
    )

    # Verify both messages are committed in one transaction.
    db.commit.assert_called_once()

    # Verify both messages are refreshed.
    db.refresh.assert_any_call(user_message)
    db.refresh.assert_any_call(assistant_message)
