from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies.db import get_session_with_user
from src.repositories.route import RouteRepository
from src.schemas.route import RouteItemStatus, RouteRead

router = APIRouter(prefix="/route", tags=["Route"])


@router.get("/courier/{courier_id}", response_model=list[RouteRead])
async def list_routes_for_courier(
    courier_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> list[RouteRead]:
    repo = RouteRepository()
    return await repo.list_by_courier(session, courier_id)


@router.get("/{route_id}/items", response_model=list[RouteItemStatus])
async def list_route_items_with_status(
    route_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> list[RouteItemStatus]:
    repo = RouteRepository()
    return await repo.list_items_with_status(session, route_id)
