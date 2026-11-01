
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from jose import jwt

from app.config.settings import settings
from app.core.security import verify_access_token


def create_test_token(payload):
    """Generate a JWT using the application's test configuration."""

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def test_verify_valid_access_token():
    """A valid token returns its subject email."""

    token = create_test_token({
        "sub": "user@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    })

    result = verify_access_token(token)

    assert result == "user@example.com"


def test_verify_invalid_access_token():
    """An invalid token raises HTTP 401."""

    with pytest.raises(HTTPException) as error:
        verify_access_token("this-is-not-a-valid-token")

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid token"


def test_verify_expired_access_token():
    """An expired token raises HTTP 401."""

    token = create_test_token({
        "sub": "user@example.com",
        "exp": datetime.now(timezone.utc) - timedelta(minutes=10),
    })

    with pytest.raises(HTTPException) as error:
        verify_access_token(token)

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid token"


def test_verify_token_without_subject():
    """A token without a subject claim raises HTTP 401."""

    token = create_test_token({
        "exp": datetime.now(timezone.utc) + timedelta(minutes=10),
    })

    with pytest.raises(HTTPException) as error:
        verify_access_token(token)

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid token"
