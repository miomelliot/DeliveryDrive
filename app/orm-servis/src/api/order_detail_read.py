# src/api/order_detail_read.py
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.dependencies.auth import get_current_user
from src.repositories.order_detail_read import OrderDetailRepository
from src.schemas.auth import CurrentUser
from src.schemas.order_detail_read import OrderDetailRead, OrderDetailUpdate

router = APIRouter(prefix="/order", tags=["Order"])


@router.get("/{order_id}", response_model=OrderDetailRead)
async def get_order_detail(
    order_id: UUID = Path(..., description="ID заказа"),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> OrderDetailRead:
    repo = OrderDetailRepository(session)
    try:
        return await repo.get_detail(order_id)
    except Exception as err:
        raise HTTPException(status_code=404, detail=str(err)) from err


@router.patch("/{order_id}")
async def update_order_detail(
    order_id: UUID = Path(..., description="ID заказа"),
    data: OrderDetailUpdate = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> dict[str, str]:
    repo = OrderDetailRepository(session)
    try:
        await repo.update_detail(order_id, data)
        return {"status": "success"}
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
