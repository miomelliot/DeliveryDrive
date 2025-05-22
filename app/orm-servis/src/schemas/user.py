# src/schemas/user.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class _UserBase(BaseModel):
    first_name: str
    last_name: str | None = None
    phone: str
    email: EmailStr
    avatar_path: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserCreate(_UserBase):
    password: str
    role_id: int


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    avatar_path: str | None = None
    password: str | None = None
    role_id: int | None = None

    model_config = ConfigDict(from_attributes=True)


class RoleRead(BaseModel):
    id: int
    name: str
    model_config = ConfigDict(from_attributes=True)


class UserRead(_UserBase):
    id: UUID
    role: RoleRead
