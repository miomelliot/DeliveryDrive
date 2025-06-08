# src/schemas/equipment.py
from pydantic import BaseModel, Field


class EquipmentCreate(BaseModel):
    # Equipment
    serial_number: str
    # HeaterType
    model: str
    price: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)
