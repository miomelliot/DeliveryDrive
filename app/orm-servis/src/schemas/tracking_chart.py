# src/schemas/tracking_chart.py
from uuid import UUID

from pydantic import BaseModel

from src.schemas.routing_chart import RoutingChartRead


class TrackingChart(BaseModel):
    route_id: UUID
    full_name: str
    orders: list[RoutingChartRead]
