# src/repositories/tables/order_status.py
from src.db.models import OrderStatus
from src.repositories.tables.base_status import BaseStatusRepository


class OrderStatusRepository(BaseStatusRepository[OrderStatus]):
    def __init__(self) -> None:
        super().__init__(OrderStatus)
