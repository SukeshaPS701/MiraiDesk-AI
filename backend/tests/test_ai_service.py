
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


# =========================================================
# DAY 46 - AI CONTEXT BUILDER TESTS
# =========================================================

def test_system_instructions_are_returned():
    service = AIService()

    instructions = service.get_system_instructions()

    assert "MiraiDesk-AI" in instructions
    assert "friendly, accurate, and concise" in instructions
    assert "conversation history" in instructions
    assert "If you are uncertain" in instructions


def test_memory_context_is_formatted():
    service = AIService()

    memory_data = {
        "favorite_language": "Python",
        "goal": "Become an AI Engineer",
    }

    context = service.build_memory_context(memory_data)

    assert "LONG-TERM USER MEMORY:" in context
    assert "favorite_language: Python" in context
    assert "goal: Become an AI Engineer" in context


def test_memory_context_handles_empty_data():
    service = AIService()

    context = service.build_memory_context({})

    assert context == ""



def test_conversation_context_uses_latest_ten_messages():
    service = AIService()

    history_data = [
        {"role": "user", "content": f"Message {i}"}
        for i in range(12)
    ]

    context = service.build_conversation_context(history_data)

    assert "user: Message 0\n" not in context
    assert "user: Message 1\n" not in context
    assert "user: Message 2\n" in context
    assert "user: Message 11\n" in context



def test_ai_prompt_contains_all_context_sections():
    service = AIService()

    message = "Explain machine learning"

    history_data = [
        {"role": "user", "content": "I am learning Python"},
        {"role": "assistant", "content": "That's great!"},
    ]

    memory_data = {
        "favorite_language": "Python",
    }

    prompt = service.build_ai_prompt(
        message=message,
        history_data=history_data,
        memory_data=memory_data,
    )

    assert "MiraiDesk-AI" in prompt
    assert "LONG-TERM USER MEMORY:" in prompt
    assert "favorite_language: Python" in prompt
    assert "RECENT CONVERSATION:" in prompt
    assert "user: I am learning Python" in prompt
    assert "assistant: That's great!" in prompt
    assert "CURRENT USER MESSAGE:" in prompt
    assert message in prompt

# =========================================================
# DAY 47 - GEMINI INTEGRATION AND RELIABILITY TESTS
# =========================================================

def test_gemini_success_returns_generated_response(ai_service):
    ai_service.api_key = "test-api-key"

    mock_response = Mock()
    mock_response.text = "Artificial Intelligence is fascinating."

    ai_service.client = Mock()
    ai_service.client.models.generate_content.return_value = mock_response

    result = ai_service.generate_ai_response(
        message="Explain AI",
        history_data=[],
        memory_data={},
    )

    assert result == "Artificial Intelligence is fascinating."
    ai_service.client.models.generate_content.assert_called_once()


def test_gemini_receives_correct_prompt(ai_service):
    ai_service.api_key = "test-api-key"

    mock_response = Mock()
    mock_response.text = "Python is a programming language."

    ai_service.client = Mock()
    ai_service.client.models.generate_content.return_value = mock_response

    ai_service.generate_ai_response(
        message="Explain Python",
        history_data=[
            {"role": "user", "content": "I am learning coding"},
        ],
        memory_data={
            "favorite_language": "Python",
        },
    )

    call_arguments = (
        ai_service.client.models.generate_content.call_args
    )

    sent_prompt = call_arguments.kwargs["contents"]

    assert "MiraiDesk-AI" in sent_prompt
    assert "Explain Python" in sent_prompt
    assert "I am learning coding" in sent_prompt
    assert "favorite_language: Python" in sent_prompt


def test_gemini_empty_response_raises_service_error(ai_service):
    ai_service.api_key = "test-api-key"

    mock_response = Mock()
    mock_response.text = ""

    ai_service.client = Mock()
    ai_service.client.models.generate_content.return_value = mock_response

    with pytest.raises(AIServiceError) as error:
        ai_service.generate_ai_response(
            message="Explain AI",
            history_data=[],
            memory_data={},
        )

    assert error.value.status_code == 502
    ai_service.client.models.generate_content.assert_called_once()


def test_gemini_retries_after_temporary_failure(
    ai_service,
    monkeypatch,
):
    ai_service.api_key = "test-api-key"

    class MockAPIError(Exception):
        def __init__(self, message, status_code):
            super().__init__(message)
            self.status_code = status_code

    mock_response = Mock()
    mock_response.text = "Gemini recovered successfully."

    ai_service.client = Mock()

    ai_service.client.models.generate_content.side_effect = [
        MockAPIError("Temporary server failure", 503),
        mock_response,
    ]

    sleep_mock = Mock()
    monkeypatch.setattr("app.ai.service.time.sleep", sleep_mock)

    result = ai_service.generate_ai_response(
        message="Explain machine learning",
        history_data=[],
        memory_data={},
    )

    assert result == "Gemini recovered successfully."

    assert (
        ai_service.client.models.generate_content.call_count == 2
    )

    sleep_mock.assert_called_once_with(1)


def test_gemini_does_not_retry_permanent_failure(
    ai_service,
    monkeypatch,
):
    ai_service.api_key = "test-api-key"

    class MockAPIError(Exception):
        def __init__(self, message, status_code):
            super().__init__(message)
            self.status_code = status_code

    ai_service.client = Mock()

    ai_service.client.models.generate_content.side_effect = (
        MockAPIError("Invalid request", 400)
    )

    sleep_mock = Mock()
    monkeypatch.setattr("app.ai.service.time.sleep", sleep_mock)

    with pytest.raises(AIServiceError) as error:
        ai_service.generate_ai_response(
            message="Explain AI",
            history_data=[],
            memory_data={},
        )

    assert error.value.status_code == 502

    ai_service.client.models.generate_content.assert_called_once()
    sleep_mock.assert_not_called()


def test_gemini_retry_exhaustion_raises_service_error(
    ai_service,
    monkeypatch,
):
    ai_service.api_key = "test-api-key"

    class MockAPIError(Exception):
        def __init__(self, message, status_code):
            super().__init__(message)
            self.status_code = status_code

    ai_service.client = Mock()

    ai_service.client.models.generate_content.side_effect = [
        MockAPIError("Server unavailable", 503),
        MockAPIError("Server unavailable", 503),
        MockAPIError("Server unavailable", 503),
    ]

    sleep_mock = Mock()
    monkeypatch.setattr("app.ai.service.time.sleep", sleep_mock)

    with pytest.raises(AIServiceError) as error:
        ai_service.generate_ai_response(
            message="Explain AI",
            history_data=[],
            memory_data={},
        )

    assert error.value.status_code == 503

    assert (
        ai_service.client.models.generate_content.call_count == 3
    )

    assert sleep_mock.call_count == 2
    sleep_mock.assert_any_call(1)
    sleep_mock.assert_any_call(2)

