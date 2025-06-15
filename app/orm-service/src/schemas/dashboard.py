# src/schemas/dashboard.py
from datetime import date

from pydantic import BaseModel


class DayCount(BaseModel):
    date: date
    count: int


class OrdersDailyResponse(BaseModel):
    items: list[DayCount]


class OrdersSummaryResponse(BaseModel):
    total: int
    completed: int
    overdue: int
    recalled: int


class WarehouseSummaryResponse(BaseModel):
    total_equipment: int
    available: int
    in_rent: int
    maintenance: int


class EquipmentStockResponse(BaseModel):
    model: str
    quantity: int
