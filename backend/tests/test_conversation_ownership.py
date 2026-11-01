
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base
from app.models import User, Conversation
from app.services.conversation_service import get_conversation


@pytest.fixture
def db_session():
    """Create an isolated in-memory SQLite database."""

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

    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_user_can_access_own_conversation(db_session):
    """A user can retrieve their own conversation."""

    user = User(
        username="user_one",
        email="user1@example.com",
        hashed_password="test-password",
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    conversation = Conversation(
        title="User One Conversation",
        user_id=user.id,
    )

    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    result = get_conversation(
        db_session,
        conversation.id,
        user.id,
    )

    assert result is not None
    assert result.id == conversation.id
    assert result.user_id == user.id


def test_user_cannot_access_another_users_conversation(db_session):
    """A user cannot retrieve a conversation owned by someone else."""

    user_one = User(
        username="user_one",
        email="user1@example.com",
        hashed_password="test-password",
    )

    user_two = User(
        username="user_two",
        email="user2@example.com",
        hashed_password="test-password",
    )

    db_session.add_all([user_one, user_two])
    db_session.commit()

    db_session.refresh(user_one)
    db_session.refresh(user_two)

    conversation = Conversation(
        title="Private Conversation",
        user_id=user_two.id,
    )

    db_session.add(conversation)
    db_session.commit()
    db_session.refresh(conversation)

    result = get_conversation(
        db_session,
        conversation.id,
        user_one.id,
    )

    assert result is None
