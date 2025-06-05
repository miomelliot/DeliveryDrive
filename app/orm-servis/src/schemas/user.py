# src/schemas/user.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class _UserBase(BaseModel):
    first_name: str
    last_name: str | None = None
    phone: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserCreate(_UserBase):
    password: str
    role_name: str


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserRead(_UserBase):
    id: UUID
    role_name: str
