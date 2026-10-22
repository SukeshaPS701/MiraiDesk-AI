
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


def create_conversation(
    db: Session,
    user_id: int,
    title: str = "New Conversation"
):
    conversation = Conversation(
        title=title,
        user_id=user_id
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def get_user_conversations(
    db: Session,
    user_id: int
):
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


def get_conversation(
    db: Session,
    conversation_id: int,
    user_id: int
):
    return (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
        .first()
    )


def add_message(
    db: Session,
    conversation_id: int,
    role: str,
    content: str,
    commit: bool = True
):
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )

    db.add(message)

    if commit:
        db.commit()
        db.refresh(message)
    else:
        db.flush()

    return message


def get_conversation_messages(
    db: Session,
    conversation_id: int
):
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
