# src/schemas/user_chart.py
from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserChartRead(BaseModel):
    id: UUID
    full_name: str  # first_name + last_name
    phone: str
    email: EmailStr
    transport_name: str
    work_schedule: str  # HH:MM-HH:MM (start_time+end_time)


class UserChartFilter(BaseModel):
    search: str | None = None
    order_by: Literal[
        "id",
        "full_name",
        "phone",
        "email",
        "transport_name",
    ] = "id"
    order_dir: Literal["asc", "desc"] = "asc"

    # 🔽 Фильтрация по диапазону времени окна
    start_time: time | None = None
    end_time: time | None = None

    limit: int = Field(default=10, le=100)
    offset: int = 0
