from pydantic import BaseModel
from typing import Literal
from datetime import datetime


class MessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True