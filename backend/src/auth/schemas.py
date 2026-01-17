from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class OwnerBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class OwnerCreate(OwnerBase):
    password: str


class OwnerResponse(OwnerBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OwnerLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int
    exp: datetime
