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


class UserManagerCreateAPI(UserCreate):
    pass


class UserManagerCreate(UserCreate):
    role_id: int | None


class UserCourierCreateAPI(UserManagerCreate):
    start_time: time = time(hour=9)
    end_time: time = time(hour=18)
    transport_name: Literal["walk", "bike", "scooter", "car", "van"] = "walk"


class UserCourierCreate(UserCourierCreateAPI):
    role_id: int | None


class UserManagerUpdate(BaseModel):
    first_name: str | None
    last_name: str | None
    phone: str | None
    email: EmailStr | None
    password_hash: str | None


class UserCourierUpdate(UserManagerUpdate):
    start_time: time | None
    end_time: time | None
    transport_name: Literal["walk", "bike", "scooter", "car", "van"] | None


class UserCourierRead(_UserBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# class _UserBase(BaseModel):
#     first_name: str
#     last_name: str | None
#     phone: str
#     email: EmailStr
#     model_config = ConfigDict(from_attributes=True)


# class _UserOutBase(_UserBase):
#     id: UUID


# class UserManagerCreate(_UserBase):
#     password: str = Field(..., min_length=8)


# class UserCourierCreate(_UserBase):
#     password: str = Field(..., min_length=8)
#     start_time: time = time(hour=9)
#     end_time: time = time(hour=18)
#     transport_name: Literal["walk", "bike", "scooter", "car", "van"] = "walk"


# class _UserUpdateBase(BaseModel):
#     first_name: str | None = None
#     last_name: str | None = None
#     phone: str | None = None
#     email: EmailStr | None = None
#     password: str | None = None
#     model_config = ConfigDict(from_attributes=True)


# class UserManagerUpdate(_UserUpdateBase):
#     pass


# class UserCourierUpdate(_UserUpdateBase):
#     start_time: time | None = None
#     end_time: time | None = None
#     transport_name: Literal["walk", "bike", "scooter", "car", "van"] | None = None


# # ----- output -----
# class UserManagerRead(_UserOutBase):
#     icon: str | None = Field(None, alias="avatar_path")


# class UserCourierRead(_UserOutBase):
#     icon: str | None = Field(None, alias="avatar_path")
#     start_time: time
#     end_time: time
#     transport_name: Literal["walk", "bike", "scooter", "car", "van"]
