# src/api/routing_selection.py
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.routing_chart_redis import RoutingChartRedis
from schemas.routing_chart import RoutingChartFilter, RoutingChartRead
from src.db.session import get_session
from src.dependencies import get_redis
from src.repositories.routing_chart import RoutingChartRepository

router = APIRouter(prefix="/routing/selection", tags=["Маршруты (Redis)"])


def get_repo(redis: Redis = Depends(get_redis)) -> RoutingChartRedis:
    return RoutingChartRedis(redis)


@router.get("/", response_model=list[RoutingChartRead])
async def get_selected_orders(
    user_id: Annotated[UUID, Query(...)],
    filters: RoutingChartFilter = Depends(),
    pg_repo: RoutingChartRepository = Depends(RoutingChartRepository),
    redis_repo: RoutingChartRedis = Depends(get_repo),
    session: AsyncSession = Depends(get_session),
) -> list[RoutingChartRead]:
    ids: list[UUID] = await redis_repo.list_ids(user_id)
    if not ids:
        return []

    return await pg_repo.get_chart(ids, filters)


@router.post("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_order(
    user_id: Annotated[UUID, Query(...)],
    order_id: UUID,
    repo: RoutingChartRedis = Depends(get_repo),
) -> None:
    await repo.add(user_id=user_id, order_id=order_id)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_order(
    user_id: Annotated[UUID, Query(...)],
    order_id: UUID,
    repo: RoutingChartRedis = Depends(get_repo),
) -> None:
    await repo.remove(user_id=user_id, order_id=order_id)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_orders(
    user_id: Annotated[UUID, Query(...)],
    repo: RoutingChartRedis = Depends(get_repo),
) -> None:
    await repo.clear(user_id=user_id)
