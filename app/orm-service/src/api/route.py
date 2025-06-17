from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import RouteItem
from src.dependencies.db import get_session_with_user
from src.repositories.route import RouteRepository as RRouteRepository
from src.repositories.tables.route import RouteRepository
from src.repositories.tables.route_item import RouteItemRepository
from src.schemas.route import RouteItemStatus, RouteRead
from src.schemas.route_item import RouteItemCreate, RouteItemRead

router = APIRouter(prefix="/route", tags=["Route"])


@router.get("/courier/{courier_id}", response_model=RouteRead)
async def list_routes_for_courier(
    courier_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> RouteRead:
    return await RRouteRepository().list_by_courier(session, courier_id)


@router.get("/{route_id}/items", response_model=list[RouteItemStatus])
async def list_route_items_with_status(
    route_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> list[RouteItemStatus]:
    repo = RRouteRepository()
    return await repo.list_items_with_status(session, route_id)


@router.post("/item", status_code=status.HTTP_201_CREATED, response_model=RouteItemRead)
async def add_route_item(
    payload: RouteItemCreate,
    session: AsyncSession = Depends(get_session_with_user),
) -> RouteItemRead:
    item: RouteItem = await RouteItemRepository().add_item(session, payload.route_id, payload.order_id)
    return RouteItemRead.model_validate(item)


@router.delete("/item/{order_id}")
async def delete_route_item(
    order_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    await RouteItemRepository().delete_by_order(session, order_id)
    return {"detail": "Маршрут обновлён"}


@router.delete("/{order_id}")
async def delete(
    route_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    await RouteRepository().delete(session, route_id)
    return {"detail": "Маршрутный лист удалён"}
