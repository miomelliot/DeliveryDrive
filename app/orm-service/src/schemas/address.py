# src/schemas/address.py
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _AddressBase(BaseModel):
    model: str
    price: float = Field(..., ge=0, examples=[599.0])
    weight: float = Field(..., ge=0, examples=[2.0])


class AddressCreate(_AddressBase):
    pass


class AddressUpdate(BaseModel):
    model: str | None = None
    price: float | None = Field(None, ge=0)
    weight: float | None = Field(None, ge=0)


class AddressRead(_AddressBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)
