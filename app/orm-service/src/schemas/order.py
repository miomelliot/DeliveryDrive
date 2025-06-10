# src/schemas/order.py
from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field


class EquipmentList(BaseModel):
    # HeaterType
    model: str
    quantity: int = Field(..., gt=0)
    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    phone: str
    name: str | None = None
    location: str = Field(min_length=5)
    window_start: time = time(9)
    window_end: time = time(18)
    rent_start: date
    rent_end: date
    comment: str | None = None

    equipment: list[EquipmentList]
    model_config = ConfigDict(from_attributes=True)
