# src/schemas/equipment_chart.py
from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EquipmentChartRead(BaseModel):
    # Equipment
    id: UUID
    # Maintenance
    date: date | None
    # HeaterType
    model: str
    weight: float
    price: float
    # Address
    location: str  # объединённый адрес: city, street, building
    # EquipmentStatus
    status: str  # description

    model_config = ConfigDict(from_attributes=True)


class EquipmentChartFilter(BaseModel):
    search: str | None = None
    order_by: Literal[
        "id",
        "model",
        "weight",
        "price",
        "location",
        "status",
    ] = "id"
    order_dir: Literal["asc", "desc"] = "asc"

    # 🔽 Фильтрация по диапазону дат (логика BETWEEN)
    date_start: date | None = None
    date_end: date | None = None

    limit: int = Field(default=10, le=100)
    offset: int = 0
