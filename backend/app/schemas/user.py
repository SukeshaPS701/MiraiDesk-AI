from pydantic import BaseModel, EmailStr
from datetime import datetime


# User Registration Request
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


# User Login Request
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# User Response
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str