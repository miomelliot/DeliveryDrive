# src/schemas/order_item.py
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
