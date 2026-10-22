
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.ai.service import AIServiceError
from app.database.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services.chat_service import ChatService


router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)


class ChatRequest(BaseModel):
    conversation_id: int
    message: str


@router.post("/")
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_service = ChatService()

    try:
        result = chat_service.chat(
            db=db,
            conversation_id=request.conversation_id,
            user_id=current_user.id,
            message=request.message,
        )
    except AIServiceError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail=str(error),
        ) from None

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    return {
        "conversation_id": result["conversation_id"],
        "user_message": {
            "id": result["user_message"].id,
            "role": result["user_message"].role,
            "content": result["user_message"].content,
        },
        "assistant_message": {
            "id": result["assistant_message"].id,
            "role": result["assistant_message"].role,
            "content": result["assistant_message"].content,
        },
    }
