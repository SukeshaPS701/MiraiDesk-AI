
from datetime import timedelta
from unittest.mock import patch

import pytest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.database.session import get_db as session_get_db
from app.core.security import create_access_token

from app.api.auth import router as auth_router
from app.api.conversations import router as conversations_router
from app.api import conversations as conversations_module
from app.api.chat import router as chat_router
from app.ai.service import AIService


# --------------------------------------------------
# TEST DATABASE AND APPLICATION
# --------------------------------------------------

@pytest.fixture
def test_app():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.create_all(bind=engine)

    app = FastAPI()

    app.include_router(auth_router)
    app.include_router(conversations_router)
    app.include_router(chat_router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[session_get_db] = override_get_db
    app.dependency_overrides[conversations_module.get_db] = override_get_db

    yield app

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def client(test_app):
    return TestClient(test_app)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def register_test_user(client):
    response = client.post(
        "/auth/register",
        json={
            "username": "senpai",
            "email": "senpai@example.com",
            "password": "StrongPassword123!",
        },
    )
    return response


def register_user(client, username, email):
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    return response.json()


def login_user(client, email):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 200
    return response.json()["access_token"]


# --------------------------------------------------
# AUTHENTICATION INTEGRATION TESTS
# --------------------------------------------------

def test_user_can_register(client):
    response = register_test_user(client)

    assert response.status_code == 200
    assert response.json()["username"] == "senpai"
    assert response.json()["email"] == "senpai@example.com"
    assert "hashed_password" not in response.json()


def test_registered_user_can_login(client):
    register_response = register_test_user(client)
    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "email": "senpai@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"
    assert login_response.json()["access_token"]


def test_user_can_access_profile_with_login_token(client):
    register_test_user(client)

    login_response = client.post(
        "/auth/login",
        json={
            "email": "senpai@example.com",
            "password": "StrongPassword123!",
        },
    )

    token = login_response.json()["access_token"]

    profile_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == "senpai@example.com"
    assert profile_response.json()["username"] == "senpai"


def test_profile_rejects_invalid_token(client):
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401


def test_profile_rejects_expired_token(client):
    register_test_user(client)

    expired_token = create_access_token(
        data={"sub": "senpai@example.com"},
        expires_delta=timedelta(seconds=-1),
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {expired_token}"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_profile_rejects_tampered_token(client):
    register_test_user(client)

    valid_token = create_access_token(
        data={"sub": "senpai@example.com"}
    )

    # Modify the token signature.
    token_parts = valid_token.split(".")

    token_parts[2] = (
        "A" if token_parts[2][0] != "A" else "B"
    ) + token_parts[2][1:]

    tampered_token = ".".join(token_parts)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {tampered_token}"
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


def test_profile_rejects_missing_token(client):
    response = client.get("/auth/me")

    assert response.status_code in (401, 403)


def test_login_rejects_wrong_password(client):
    register_test_user(client)

    response = client.post(
        "/auth/login",
        json={
            "email": "senpai@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


# --------------------------------------------------
# REGISTRATION EDGE-CASE TESTS
# --------------------------------------------------

def test_registration_rejects_duplicate_email(client):
    register_user(
        client,
        "first_user",
        "duplicate@example.com",
    )

    response = client.post(
        "/auth/register",
        json={
            "username": "second_user",
            "email": "duplicate@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_registration_rejects_duplicate_username(client):
    register_user(
        client,
        "duplicate_user",
        "first@example.com",
    )

    response = client.post(
        "/auth/register",
        json={
            "username": "duplicate_user",
            "email": "second@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"


# --------------------------------------------------
# CONVERSATION OWNERSHIP SECURITY TESTS
# --------------------------------------------------

def test_user_cannot_access_another_users_conversation(client):
    register_user(client, "user_a", "usera@example.com")
    register_user(client, "user_b", "userb@example.com")

    token_a = login_user(client, "usera@example.com")
    token_b = login_user(client, "userb@example.com")

    # User A creates a conversation.
    create_response = client.post(
        "/conversations/",
        json={"title": "User A private conversation"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert create_response.status_code == 200

    conversation_id = create_response.json()["id"]

    # User B attempts to access User A's conversation.
    response = client.get(
        f"/conversations/{conversation_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


def test_user_cannot_access_another_users_messages(client):
    register_user(client, "user_a", "usera@example.com")
    register_user(client, "user_b", "userb@example.com")

    token_a = login_user(client, "usera@example.com")
    token_b = login_user(client, "userb@example.com")

    create_response = client.post(
        "/conversations/",
        json={"title": "Private messages"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    conversation_id = create_response.json()["id"]

    # User A creates a private message.
    message_response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "role": "user",
            "content": "This is private information.",
        },
        headers={"Authorization": f"Bearer {token_a}"},
    )

    assert message_response.status_code == 200

    # User B attempts to retrieve the messages.
    response = client.get(
        f"/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 404


def test_user_cannot_add_message_to_another_users_conversation(client):
    register_user(client, "user_a", "usera@example.com")
    register_user(client, "user_b", "userb@example.com")

    token_a = login_user(client, "usera@example.com")
    token_b = login_user(client, "userb@example.com")

    create_response = client.post(
        "/conversations/",
        json={"title": "User A conversation"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    conversation_id = create_response.json()["id"]

    response = client.post(
        f"/conversations/{conversation_id}/messages",
        json={
            "role": "user",
            "content": "Unauthorized message",
        },
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 404


def test_chat_does_not_invoke_ai_for_another_users_conversation(client):
    register_user(client, "user_a", "usera@example.com")
    register_user(client, "user_b", "userb@example.com")

    token_a = login_user(client, "usera@example.com")
    token_b = login_user(client, "userb@example.com")

    create_response = client.post(
        "/conversations/",
        json={"title": "Private AI conversation"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    conversation_id = create_response.json()["id"]

    # Ensure AI generation is never called for unauthorized access.
    with patch.object(
        AIService,
        "generate_response",
        autospec=True,
    ) as mock_generate:

        response = client.post(
            "/chat/",
            json={
                "conversation_id": conversation_id,
                "message": "Try to access this conversation.",
            },
            headers={"Authorization": f"Bearer {token_b}"},
        )

        assert response.status_code == 404
        mock_generate.assert_not_called()
