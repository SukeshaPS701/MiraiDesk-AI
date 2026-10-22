from typing import Generic, TypeVar

from pydantic import BaseModel, Field, field_validator


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: T


class MemoryCreate(BaseModel):
    memory_type: str = Field(
        ...,
        min_length=2,
        max_length=50
    )

    content: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )

    @field_validator("memory_type", "content")
    @classmethod
    def validate_not_blank(cls, value: str):
        if not value.strip():
            raise ValueError("Field cannot be blank")

        return value.strip()


class MemoryResponse(BaseModel):
    id: int
    user_id: int
    memory_type: str
    content: str

    class Config:
        from_attributes = True