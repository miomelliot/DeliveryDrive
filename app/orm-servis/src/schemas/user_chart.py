# src/schemas/user_chart.py
from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserChartRead(BaseModel):
    id: UUID
    first_name: str
    last_name: str | None = None
    phone: str
    email: EmailStr
    transport_name: str
    start_time: time
    end_time: time


class UserChartFilter(BaseModel):
    search: str | None = None
    order_by: Literal[
        "id",
        "first_name",
        "last_name",
        "phone",
        "email",
        "transport_name",
        "start_time",
        "end_time",
    ] = "first_name"
    order_dir: Literal["asc", "desc"] = "asc"
    limit: int = Field(default=10, le=100)
    offset: int = 0
