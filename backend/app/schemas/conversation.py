from pydantic import BaseModel
from datetime import datetime


class ConversationCreate(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True