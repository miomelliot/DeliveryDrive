# src/schemas/logistics.py
from datetime import time
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressRead(BaseModel):
    id: UUID
    city: str
    street: str | None
    building: str
    lat: float = 0.0
    lon: float = 0.0


class Solver(BaseModel):
    max_runtime_sec: int = 250
    num_solutions: int = 1
    allow_waiting: bool = True
    time_window_penalty: int = 10


class TransportType(BaseModel):
    name: str
    avg_speed: float
    capacity: float


class CreateSchema(BaseModel):
    courier_id: UUID
    time_window: list[time]
    transport_type: TransportType

    @field_validator("time_window")
    @classmethod
    def validate_time_window(cls, v: list[time]) -> list[time]:
        if len(v) != 2:
            raise ValueError("time_window должен содержать [start, end]")
        return v


class OrderSchema(BaseModel):
    order_id: UUID
    address: AddressRead
    weight: float
    service_duration: int = Field(default=1500)
    time_window: list[time]

    @field_validator("time_window")
    @classmethod
    def validate_time_window(cls, v: list[time]) -> list[time]:
        if len(v) != 2:
            raise ValueError("time_window должен содержать [start, end]")
        return v


class Logistics(BaseModel):
    warehouse: AddressRead
    orders: list[OrderSchema]
    creates: list[CreateSchema]
    solver: Solver = Solver()
    osrm_profile: Literal["driving", "foot", "bike"] = "driving"

    model_config = ConfigDict(from_attributes=True)
