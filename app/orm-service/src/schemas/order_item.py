# src/schemas/order_item.py
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class _OrderItemBase(BaseModel):
    order_id: UUID
    heater_type_id: int
    quantity: int


class OrderItemCreate(_OrderItemBase):
    pass


class OrderItemUpdate(BaseModel):
    quantity: int | None


class OrderItemRead(_OrderItemBase):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


class OrderItemDetailed(BaseModel):
    serial_number: str
    model: str
    price: Decimal
    weight: float
    quantity: int

    model_config = ConfigDict(from_attributes=True)
