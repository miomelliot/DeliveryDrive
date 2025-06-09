# src/schemas/equipment.py
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EquipmentCreate(BaseModel):
    # Equipment
    serial_number: str
    # HeaterType
    model: str
    price: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)

    model_config = ConfigDict(from_attributes=True)


class EquipmentRead(BaseModel):
    model: str
    price: float
    weight: float
    count: int
    count_available: int

    model_config = ConfigDict(from_attributes=True)


class EquipmentFilter(BaseModel):
    status: Literal["rented", "maintenance", "available", "decommissioned"] | None = None
    model_config = ConfigDict(from_attributes=True)
