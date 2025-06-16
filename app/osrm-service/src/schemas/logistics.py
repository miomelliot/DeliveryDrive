# src/schemas/logistics.py
from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.schemas.address import AddressRead


class Solver(BaseModel):
    max_runtime_sec: int = 30
    num_solutions: int = 1
    allow_waiting: bool = True


class TransportType(BaseModel):
    name: str
    avg_speed: float
    capacity: float


class Create(BaseModel):
    time_window: list[time]
    transport_type: TransportType


class Order(BaseModel):
    order_id: UUID
    address: AddressRead
    weight: float
    service_duration: int = Field(default=1500)
    time_window: list[time]


class Logistics(BaseModel):
    orders: list[Order]
    creates: list[Create]
    solver: Solver
    osrm_profile: Literal["driving", "foot", "bike"] = "driving"
