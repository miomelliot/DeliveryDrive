from datetime import datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RoutingChartRead(BaseModel):
    id: UUID
    rent_start: datetime
    rent_end: datetime
    window: str  # HH:MM-HH:MM (window_start_from+window_end_to)
    phone: str
    location: str  # объединённый адрес: city, street, building
    description: str  # статус заказа


class RoutingChartFilter(BaseModel):
    search: str | None = None
    order_by: Literal[
        "id",
        "rent_start",
        "rent_end",
        "phone",
        "location",
        "description",
    ] = "id"
    order_dir: Literal["asc", "desc"] = "asc"

    route_id: UUID | None = None

    # 📋 Выпадающий фильтр по статусу заказа
    description: str | None = None

    # ⏰ Фильтрация по временному окну
    window_start_from: time | None = None
    window_end_to: time | None = None

    only_active: bool = True

    limit: int = Field(default=10, le=100)
    offset: int = 0
