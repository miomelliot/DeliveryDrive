# src/schemas/order.py
from datetime import date, time

from pydantic import BaseModel, Field


class EquipmentList(BaseModel):
    # HeaterType
    model: str = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    phone: str = Field(
        ...,
        min_length=10,
        max_length=12,
    )
    name: str | None = None
    location: str = Field(min_length=5)  # объединённый адрес: city, street, building распарсить по , макс 3 элемента
    window_start: time = time(9)
    window_end: time = time(18)
    rent_start: date
    rent_end: date
    comment: str | None = None

    equipment: list[EquipmentList]
