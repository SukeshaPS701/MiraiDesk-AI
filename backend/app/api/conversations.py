from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import SessionLocal

from app.dependencies.auth import get_current_user
from app.models.user import User

from app.services.conversation_service import (
    create_conversation,
    get_user_conversations,
    get_conversation,
    get_conversation_messages,
    add_message,
)

from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
)

from app.schemas.message import (
    MessageCreate,
    MessageResponse,
)


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# CREATE CONVERSATION
# --------------------------------------------------

@router.post(
    "/",
    response_model=ConversationResponse,
)
def create_new_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_conversation(
        db,
        current_user.id,
        conversation.title,
    )


# --------------------------------------------------
# GET USER CONVERSATIONS
# --------------------------------------------------

@router.get(
    "/",
    response_model=list[ConversationResponse],
)
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversations = get_user_conversations(
        db,
        current_user.id,
    )

    return conversations


# --------------------------------------------------
# GET SINGLE CONVERSATION
# --------------------------------------------------

@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def get_single_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = get_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return conversation


# --------------------------------------------------
# GET CONVERSATION MESSAGES
# --------------------------------------------------

@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageResponse],
)
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = get_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    messages = get_conversation_messages(
        db,
        conversation_id,
    )

    return messages


# --------------------------------------------------
# CREATE MESSAGE
# --------------------------------------------------

@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
)
def create_message(
    conversation_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = get_conversation(
        db,
        conversation_id,
        current_user.id,
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return add_message(
        db,
        conversation_id,
        message.role,
        message.content,
    )