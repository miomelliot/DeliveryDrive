from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class _UserInBase(BaseModel):
    first_name: str
    last_name: str | None
    phone: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class _UserOutBase(_UserInBase):
    id: UUID


class UserManagerCreate(_UserInBase):
    password: str = Field(..., min_length=8)


class UserCourierCreate(_UserInBase):
    password: str = Field(..., min_length=8)
    start_time: time = time(hour=9)
    end_time: time = time(hour=18)
    transport_name: Literal["walk", "bike", "scooter", "car", "van"] = "walk"


class _UserUpdateBase(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    model_config = ConfigDict(from_attributes=True)


class UserManagerUpdate(_UserUpdateBase):
    pass


class UserCourierUpdate(_UserUpdateBase):
    start_time: time | None = None
    end_time: time | None = None
    transport_name: Literal["walk", "bike", "scooter", "car", "van"] | None = None


class UserManagerRead(_UserOutBase):
    icon: str | None = Field(None, alias="avatar_path")


class UserCourierRead(_UserOutBase):
    icon: str | None = Field(None, alias="avatar_path")
    start_time: time
    end_time: time
    transport_name: Literal["walk", "bike", "scooter", "car", "van"]
