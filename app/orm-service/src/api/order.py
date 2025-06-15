# src/api/order.py
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, File, Path, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Order
from src.dependencies.db import get_session_with_user
from src.repositories.charts.order_chart import OrderChartRepository
from src.repositories.charts.order_detail_read import OrderDetailRepository
from src.repositories.tables.order import OrderRepository
from src.schemas.order import OrderCreateAPI
from src.schemas.order_detail_read import OrderDetailRead, OrderDetailUpdate

router = APIRouter(prefix="/order", tags=["Order"])


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    data: OrderCreateAPI,
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    order: Order = await OrderRepository().create_raw(session, data)
    return {"id": str(order.id), "detail": "Заказ успешно создан"}


@router.get("/{order_id}", response_model=OrderDetailRead)
async def get_order_detail(
    order_id: UUID = Path(..., description="ID заказа"),
    session: AsyncSession = Depends(get_session_with_user),
) -> OrderDetailRead:
    return await OrderDetailRepository(session).get_detail(order_id)


@router.patch("/{order_id}")
async def update_order_detail(
    order_id: UUID = Path(..., description="ID заказа"),
    data: OrderDetailUpdate = Body(...),
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    await OrderDetailRepository(session).update_detail(order_id, data)
    return {"detail": "Заказ обновлён"}


@router.delete("/{order_id}")
async def delete_order(
    order_id: UUID,
    session: AsyncSession = Depends(get_session_with_user),
) -> dict[str, str]:
    await OrderRepository().delete(session, order_id)
    return {"detail": "Заказ удалён"}


# ────────────────────────────── Bulk Import ──────────────────────────────
@router.post(
    "/import",
    status_code=status.HTTP_201_CREATED,
    summary="Импорт заказов из файла (Excel / CSV / JSON)",
)
async def import_orders(
    file: UploadFile = File(..., description="orders_import.xlsx | .csv | .json"),
    session: AsyncSession = Depends(get_session_with_user),
) -> list[dict[str, Any]]:
    created: list[Order] = await OrderRepository().import_file(session, file)
    return [{"id": str(order.id), "client": order.client_id} for order in created]


# ────────────────────────────── Lookup helpers ──────────────────────────────
@router.get("/status", response_model=list[str])
async def get_order_status(
    session: AsyncSession = Depends(get_session_with_user),
) -> list[str]:
    return await OrderChartRepository(session).get_unique_descriptions()


@router.get("/courier-name", response_model=list[str])
async def get_courier_full_names(
    session: AsyncSession = Depends(get_session_with_user),
) -> list[str]:
    return await OrderChartRepository(session).get_unique_full_names()
