# src/schemas/OrderItem_item.py
from src.db.models import OrderItem
from src.repositories.tables.base import CRUDRepository
from src.schemas.order_item import OrderItemCreate, OrderItemUpdate


class OrderItemRepository(CRUDRepository[OrderItem, OrderItemCreate, OrderItemUpdate]):
    def __init__(self) -> None:
        super().__init__(OrderItem)
