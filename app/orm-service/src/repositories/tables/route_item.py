from typing import Tuple
from uuid import UUID

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import RouteItem
from src.repositories.tables.base import CRUDRepository
from src.schemas.route_item import RouteItemCreate, RouteItemUpdate
from src.utils.http_error import NotFoundError


class RouteItemRepository(CRUDRepository[RouteItem, RouteItemCreate, RouteItemUpdate]):
    def __init__(self) -> None:
        super().__init__(RouteItem)

    async def add_item(self, session: AsyncSession, route_id: UUID, order_id: UUID) -> RouteItem:
        stmt: Select[Tuple[int]] = select(func.max(RouteItem.sequence)).where(RouteItem.route_id == route_id)
        last_seq: int | None = await session.scalar(stmt)
        item = RouteItem(route_id=route_id, order_id=order_id, sequence=(last_seq or -1) + 1)
        session.add(item)
        await session.flush()
        await session.refresh(item)
        return item

    async def delete_by_order(self, session: AsyncSession, order_id: UUID) -> None:
        exists_stmt: Select[Tuple[UUID]] = select(RouteItem.id).where(RouteItem.order_id == order_id)
        exists: UUID | None = await session.scalar(exists_stmt)
        if exists is None:
            raise NotFoundError("Маршрутный пункт не найден")

        await session.execute(delete(RouteItem).where(RouteItem.order_id == order_id))
