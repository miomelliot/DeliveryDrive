# src/schemas/equipment.py
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _EquipmentBase(BaseModel):
    heater_type_id: int
    serial_number: str
    equipment_status_id: int
    warehouse_id: UUID
    current_address_id: UUID


class EquipmentCreate(_EquipmentBase):
    pass


class EquipmentUpdate(BaseModel):
    heater_type_id: int | None
    serial_number: str | None
    equipment_status_id: int | None
    warehouse_id: UUID | None
    current_address_id: UUID | None


class EquipmentRead(_EquipmentBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class EquipmentCreateAPI(BaseModel):
    # Equipment
    serial_number: str
    # HeaterType
    model: str
    price: float = Field(..., gt=0)
    weight: float = Field(..., gt=0)

    model_config = ConfigDict(from_attributes=True)


class EquipmentReadAPI(BaseModel):
    model: str
    price: float
    weight: float
    count: int
    count_available: int

    model_config = ConfigDict(from_attributes=True)


class EquipmentFilter(BaseModel):
    status: Literal["rented", "maintenance", "available", "decommissioned"] | None = None
    model_config = ConfigDict(from_attributes=True)
