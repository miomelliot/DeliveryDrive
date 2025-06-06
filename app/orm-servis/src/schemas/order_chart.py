# src/schemas/order_chart.py
from datetime import datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class OrderChartRead(BaseModel):
    # Order
    id: UUID
    created_at: datetime
    rent_start: datetime
    rent_end: datetime
    window_start: time
    window_end: time
    # Client
    phone: str
    # Address
    city: str
    street: str
    building: str
    # OrderStatus
    description: str
    # User
    first_name: str | None
    last_name: str | None


class OrderChartFilter(BaseModel):
    search: str | None = None
    order_by: Literal[
        "id",
        "created_at",
        "rent_start",
        "rent_end",
        "phone",
        "city",
        "street",
        "building",
    ] = "id"
    order_dir: Literal["asc", "desc"] = "asc"

    # 🔽 Выпадающий фильтр по имени и описанию статуса
    description: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    # 🔽 Фильтрация по диапазону времени окна
    window_start_from: time | None = None
    window_end_to: time | None = None

    only_active: bool = True

    limit: int = Field(default=10, le=100)
    offset: int = 0
