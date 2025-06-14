# src/schemas/user.py
from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class _UserBase(BaseModel):
    first_name: str
    last_name: str | None
    phone: str
    email: EmailStr


class UserCreate(_UserBase):
    password_hash: str = Field(min_length=8)
    role_id: int


class UserCreateAPI(_UserBase):
    password: str = Field(min_length=8)


class UserCourierCreateAPI(UserCreateAPI):
    start_time: time = time(hour=9)
    end_time: time = time(hour=18)
    transport_name: Literal["walk", "bike", "scooter", "car", "van"] = "walk"


class UserUpdate(BaseModel):
    first_name: str | None
    last_name: str | None
    phone: str | None
    email: EmailStr | None
    password_hash: str | None


class UserUpdateAPI(BaseModel):
    first_name: str | None
    last_name: str | None
    phone: str | None
    email: EmailStr | None
    password: str | None


class UserRead(_UserBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class _UserOutBase(_UserBase):
    id: UUID


class UserManagerRead(_UserOutBase):
    icon: str | None = Field(None, alias="avatar_path")


class UserCourierRead(_UserOutBase):
    icon: str | None = Field(None, alias="avatar_path")
    start_time: time
    end_time: time
    transport_name: str
