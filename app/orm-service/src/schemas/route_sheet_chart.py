# src/schemas/route_sheet_chart.py
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RouteSheetChart(BaseModel):
    id: UUID
    full_name: str
    count_orders: int
    status: int  # Процент выполнения (0–100)

    model_config = ConfigDict(from_attributes=True)


class RouteSheetChartFilter(BaseModel):
    search: str | None = None
    order_by: Literal["id", "full_name", "count_orders"] = "id"
    order_dir: Literal["asc", "desc"] = "asc"

    limit: int = Field(default=10, le=100)
    offset: int = 0
