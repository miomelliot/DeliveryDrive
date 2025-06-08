# src/schemas/user.py
from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, FilePath


# ─────────────────────── Base Schemas ───────────────────────
class UserBase(BaseModel):
    first_name: str
    last_name: str | None
    phone: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserUpdateBase(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    model_config = ConfigDict(from_attributes=True)


# ─────────────────────── Create Schemas ───────────────────────
class UserManagerCreate(UserBase):
    password: str
    # icon: UploadFile


class UserCourierCreate(UserBase):
    password: str
    start_time: time = time(hour=9, minute=0)
    end_time: time = time(hour=18, minute=0)
    transport_name: Literal["walk", "bike", "scooter", "car", "van"] = "walk"
    # icon: UploadFile


# ─────────────────────── Update Schemas ───────────────────────
class UserManagerUpdate(UserUpdateBase):
    pass
    # icon: UploadFile


class UserCourierUpdate(UserUpdateBase):
    start_time: time | None = None
    end_time: time | None = None
    transport_name: Literal["walk", "bike", "scooter", "car", "van"] | None = None
    # icon: UploadFile


# ─────────────────────── Read Schemas ───────────────────────
class UserManagerRead(UserBase):
    icon: FilePath


class UserCourierRead(UserBase):
    icon: FilePath
    start_time: time
    end_time: time
    transport_name: Literal["walk", "bike", "scooter", "car", "van"]
