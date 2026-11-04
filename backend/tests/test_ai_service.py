
from unittest.mock import Mock

import pytest

from app.ai.service import AIService, AIServiceError


@pytest.fixture
def ai_service():
    """Create an AI service without requiring a real Gemini API key."""
    service = AIService()
    service.api_key = None
    service.client = None
    return service


def test_empty_message_returns_validation_response(ai_service):
    result = ai_service.generate_response("   ")

    assert result == "Please provide a message."


def test_greeting_returns_basic_response(ai_service):
    result = ai_service.generate_response("Hello")

    assert "Hello Senpai!" in result
    assert "MiraiDesk-AI" in result


def test_who_are_you_returns_basic_response(ai_service):
    result = ai_service.generate_response("Who are you?")

    assert "MiraiDesk-AI" in result
    assert "desktop assistant" in result


def test_memory_statement_detects_favorite_language(ai_service):
    result = ai_service.detect_memory_statement(
        "My favorite programming language is Python",
        "my favorite programming language is python",
    )

    assert result is not None
    assert "Python" in result


def test_memory_statement_detects_goal(ai_service):
    result = ai_service.detect_memory_statement(
        "My goal is to become an AI engineer",
        "my goal is to become an ai engineer",
    )

    assert result is not None
    assert "AI engineer" in result


def test_memory_question_returns_saved_language(ai_service):
    result = ai_service.get_memory_response(
        "what is my favorite programming language?",
        {"favorite_language": "Python"},
    )

    assert result == "Your favorite programming language is Python."


def test_memory_question_handles_missing_goal(ai_service):
    result = ai_service.get_memory_response(
        "what is my goal?",
        {},
    )

    assert result == "I don't think you've told me your goal yet."


def test_conversation_history_is_formatted(ai_service):
    message = Mock()
    message.role = "user"
    message.content = "Hello MiraiDesk"

    result = ai_service.format_conversation_history([message])

    assert result == [
        {
            "role": "user",
            "content": "Hello MiraiDesk",
        }
    ]


def test_memories_are_formatted(ai_service):
    memory = Mock()
    memory.memory_type = "favorite_language"
    memory.content = "Python"

    result = ai_service.format_memories([memory])

    assert result == {"favorite_language": "Python"}


def test_gemini_missing_api_key_raises_service_error(ai_service):
    with pytest.raises(AIServiceError) as error:
        ai_service.generate_ai_response(
            message="Explain AI",
            history_data=[],
            memory_data={},
        )

    assert error.value.status_code == 503
    assert str(error.value) == "AI service is not configured."
    
def test_recent_user_messages_returns_latest_user_messages(ai_service):
    history = [
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First answer"},
        {"role": "user", "content": "Second question"},
        {"role": "assistant", "content": "Second answer"},
        {"role": "user", "content": "Third question"},
    ]

    result = ai_service.get_recent_user_messages(history, limit=2)

    assert result == ["Third question", "Second question"]


def test_gemini_unavailable_raises_service_error(ai_service):
    ai_service.api_key = "test-api-key"
    ai_service.client = None

    with pytest.raises(AIServiceError) as error:
        ai_service.generate_ai_response(
            message="Explain artificial intelligence",
            history_data=[],
            memory_data={},
        )

    assert error.value.status_code == 503
    assert str(error.value) == "AI service is not available."

