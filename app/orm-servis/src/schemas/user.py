# src/schemas/user.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict

class _UserBase(BaseModel):
    first_name: str
    last_name: str | None = None
    phone: str
    email: EmailStr
    avatar_path: str | None = None
    model_config = ConfigDict(from_attributes=True)

class UserCreate(_UserBase):
    password: str

class UserUpdate(_UserBase):
    password: str | None = None

class UserRead(_UserBase):
    id: UUID
    role_id: int
    created_at: datetime
