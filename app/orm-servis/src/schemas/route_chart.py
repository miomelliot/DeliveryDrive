# src/schemas/route_chart.py
from datetime import datetime, time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class RouteChart(BaseModel):
    # Route
    id: UUID
    date: datetime
    # User
    full_name: str
    # SQL
    count_orders: int
    status: int  # Процент выполнения (0–100)


class RouteChartFilter(BaseModel):
    search: str | None = None
    order_by: Literal[
        "id",
        "date",
        "full_name",
        "count_orders",
    ] = "id"
    order_dir: Literal["asc", "desc"] = "asc"

    # 🔽 Фильтрация по диапазону времени окна
    date_start: time | None = None
    date_end: time | None = None

    only_active: bool = True

    limit: int = Field(default=10, le=100)
    offset: int = 0
