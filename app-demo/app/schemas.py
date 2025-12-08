from datetime import datetime

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    username: str = Field(..., max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

