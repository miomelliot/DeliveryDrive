# src/schemas/address.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _AddressBase(BaseModel):
    city: str
    street: str | None
    building: str
    lat: float = 0.0
    lon: float = 0.0


class AddressCreate(BaseModel):
    location: str = Field(..., min_length=5)


class AddressUpdate(BaseModel):
    location: str | None = None


class AddressRead(_AddressBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
