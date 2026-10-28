
from unittest.mock import Mock
from app.dependencies.auth import get_current_user
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.ai.service import AIServiceError
from app.api import chat as chat_module


def create_test_app():
    """Create an isolated FastAPI app for chat API tests."""

    app = FastAPI()
    app.include_router(chat_module.router)

    # Mock authentication so no real login or token is needed.
    app.dependency_overrides[
        chat_module.get_current_user
    ] = lambda: Mock(id=2)

    # Mock database dependency to avoid a real DB session.
    app.dependency_overrides[
        chat_module.get_db
    ] = lambda: Mock()

    return app


def test_chat_api_success(monkeypatch):
    """Successful chat requests return both messages."""

    user_message = Mock(
        id=101,
        role="user",
        content="Hello!",
    )

    assistant_message = Mock(
        id=102,
        role="assistant",
        content="Hello! How can I help?",
    )

    service = Mock()
    service.chat.return_value = {
        "conversation_id": 13,
        "user_message": user_message,
        "assistant_message": assistant_message,
    }

    monkeypatch.setattr(
        chat_module,
        "ChatService",
        Mock(return_value=service),
    )

    app = create_test_app()

    with TestClient(app) as client:
        response = client.post(
            "/chat/",
            json={
                "conversation_id": 13,
                "message": "Hello!",
            },
        )

    assert response.status_code == 200

    assert response.json() == {
        "conversation_id": 13,
        "user_message": {
            "id": 101,
            "role": "user",
            "content": "Hello!",
        },
        "assistant_message": {
            "id": 102,
            "role": "assistant",
            "content": "Hello! How can I help?",
        },
    }

    service.chat.assert_called_once()


def test_chat_api_ai_failure_returns_503(monkeypatch):
    """AI service failures become HTTP error responses."""

    service = Mock()
    service.chat.side_effect = AIServiceError(
        "AI service temporarily unavailable",
        status_code=503,
    )

    monkeypatch.setattr(
        chat_module,
        "ChatService",
        Mock(return_value=service),
    )

    app = create_test_app()

    with TestClient(app) as client:
        response = client.post(
            "/chat/",
            json={
                "conversation_id": 13,
                "message": "Explain quantum computing.",
            },
        )

    assert response.status_code == 503
    assert response.json() == {
        "detail": "AI service temporarily unavailable"
    }

    service.chat.assert_called_once()


def test_chat_api_missing_conversation_returns_404(
    monkeypatch,
):
    """A missing or inaccessible conversation returns HTTP 404."""

    service = Mock()
    service.chat.return_value = None

    monkeypatch.setattr(
        chat_module,
        "ChatService",
        Mock(return_value=service),
    )

    app = create_test_app()

    with TestClient(app) as client:
        response = client.post(
            "/chat/",
            json={
                "conversation_id": 99999,
                "message": "Hello!",
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Conversation not found"
    }

    service.chat.assert_called_once()
def test_chat_api_missing_message_returns_422(monkeypatch):
    """Requests without a message return a validation error."""

    app = create_test_app()

    with TestClient(app) as client:
        response = client.post(
            "/chat/",
            json={"conversation_id": 13},
        )

    assert response.status_code == 422


def test_chat_api_invalid_conversation_id_returns_422():
    """A non-integer conversation ID is rejected."""

    app = create_test_app()

    with TestClient(app) as client:
        response = client.post(
            "/chat/",
            json={
                "conversation_id": "not-an-integer",
                "message": "Hello!",
            },
        )

    assert response.status_code == 422
def test_validation_error_response_has_expected_structure():
    """Validation errors use the structured API error format."""

    app = FastAPI()

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        safe_details = []

        for error in exc.errors():
            safe_details.append({
                "type": error.get(
                    "type",
                    "validation_error",
                ),
                "loc": list(error.get("loc", ())),
                "msg": error.get(
                    "msg",
                    "Invalid input.",
                ),
            })

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": safe_details,
                },
            },
        )

    @app.post("/validation-test")
    def validation_test(payload: dict):
        return {"success": True}

    with TestClient(app) as client:
        response = client.post(
            "/validation-test",
            json=None,
        )

    assert response.status_code == 422

    data = response.json()

    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Request validation failed."
    assert isinstance(data["error"]["details"], list)
    assert len(data["error"]["details"]) > 0

def create_auth_test_app():
    """Create an isolated app using the real auth dependency."""

    app = FastAPI()
    app.include_router(chat_module.router)

    app.dependency_overrides[
        chat_module.get_db
    ] = lambda: Mock()

    return app


def test_chat_api_without_token_returns_401():
    """Requests without a bearer token are rejected."""

    app = create_auth_test_app()

    with TestClient(app) as client:
        response = client.post(
            "/chat/",
            json={
                "conversation_id": 13,
                "message": "Hello!",
            },
        )

    assert response.status_code == 401


def test_auth_user_not_found_returns_401(monkeypatch):
    """A valid token for an unknown user is rejected."""

    from app.dependencies import auth as auth_module

    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = None

    app = create_auth_test_app()

    app.dependency_overrides[
        chat_module.get_db
    ] = lambda: db

    monkeypatch.setattr(
        auth_module,
        "verify_access_token",
        lambda token: "missing@example.com",
    )

    with TestClient(app) as client:
        response = client.post(
            "/chat/",
            headers={"Authorization": "Bearer test-token"},
            json={
                "conversation_id": 13,
                "message": "Hello!",
            },
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "User not found"}
