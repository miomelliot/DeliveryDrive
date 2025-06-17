# src/schemas/order_chart.py
from datetime import date, datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrderChartRead(BaseModel):
    # Order
    id: UUID
    created_at: datetime
    rent_start: datetime
    rent_end: datetime
    window: str  # HH:MM-HH:MM (window_start_from+window_end_to)
    # Client
    phone: str
    # Address
    location: str  # объединённый адрес: city, street, building
    # OrderStatus
    status: str  # статус заказа
    # User
    full_name: str | None  # first_name + last_name

    model_config = ConfigDict(from_attributes=True)


class OrderChartFilter(BaseModel):
    search: str | None = None
    order_by: Literal[
        "id",
        "created_at",
        "rent_start",
        "rent_end",
        "phone",
        "location",
        "status",
        "full_name",
    ] = "id"
    order_dir: Literal["asc", "desc"] = "asc"

    # 🔽 Выпадающий фильтр по имени и описанию статуса
    status: (
        Literal[
            "Новый",
            "Запланирован",
            "В доставке",
            "В аренде",
            "Завершён",
            "Отменён",
            "В обработке",
        ]
        | None
    ) = None
    rent_start: date | None = None

    # 🔽 Фильтрация по диапазону времени окна
    window_start_from: time | None = None
    window_end_to: time | None = None

    only_active: bool = True

    limit: int = Field(default=10, le=100)
    offset: int = 0
