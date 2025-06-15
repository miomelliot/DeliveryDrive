# src/schemas/warehouse.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _WarehouseBase(BaseModel):
    address_id: UUID


class WarehouseCreateAPI(BaseModel):
    location: str = Field(..., min_length=5, examples=["Москва, Ленинский проспект, 37А"])


class WarehouseCreate(_WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    address_id: UUID


class WarehouseRead(_WarehouseBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
