# src/schemas/order.py
from datetime import date, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class _OrderBase(BaseModel):
    client_id: UUID
    window_start: time = Field(default=time(9))
    window_end: time = Field(default=time(9))
    rent_start: date
    rent_end: date
    status_id: int
    comment: str | None = None


class OrderCreate(_OrderBase):
    pass


class OrderUpdate(BaseModel):
    window_start: time | None
    window_end: time | None
    rent_start: date | None
    rent_end: date | None
    status_id: int | None
    comment: str | None


class OrderRead(_OrderBase):
    id: UUID

    model_config = ConfigDict(from_attributes=True)


class EquipmentList(BaseModel):
    model: str
    quantity: int = Field(..., gt=0)

    model_config = ConfigDict(from_attributes=True)


class OrderCreateAPI(BaseModel):
    phone: str
    name: str | None = None
    location: str = Field(min_length=5, examples=["Москва, Ленинский проспект, 37А"])
    window_start: time = time(9)
    window_end: time = time(18)
    rent_start: date
    rent_end: date
    comment: str | None = None
    equipment: list[EquipmentList]

    model_config = ConfigDict(from_attributes=True)


class OrderDetailUpdate(BaseModel):
    phone: str | None = None
    client_name: str | None = None
    rent_start: date | None = None
    rent_end: date | None = None
    window_start: time | None
    window_end: time | None
    location: str | None = None
    status: str | None = None
    invoice_status: str | None = None
    invoice_issued_at: date | None = None
    invoice_paid_at: date | None = None
    comment: str | None = None

    model_config = ConfigDict(from_attributes=True)
