# src/schemas/address.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _AddressBase(BaseModel):
    city: str
    street: str | None
    building: str
    lat: float = 0.0
    lon: float = 0.0


class AddressCreateAPI(BaseModel):
    location: str = Field(..., min_length=5)


class AddressUpdateAPI(BaseModel):
    location: str | None


class AddressCreate(_AddressBase):
    pass


class AddressUpdate(BaseModel):
    city: str | None
    street: str | None
    building: str | None
    lat: float | None
    lon: float | None


class AddressRead(_AddressBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
