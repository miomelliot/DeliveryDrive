# src/repositories/utils.py
from datetime import datetime
from datetime import timezone as tz
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import OrderHistory


async def add_order_history(
    session: AsyncSession,
    *,
    order_id: UUID,
    previous_status_id: int | None,
    new_status_id: int,
    user_id: UUID,
) -> None:
    """Создать запись в order_history и сразу flush-нуть."""
    session.add(
        OrderHistory(
            order_id=order_id,
            previous_status_id=previous_status_id,
            new_status_id=new_status_id,
            user_id=user_id,
            timestamp=datetime.now(tz=tz.utc),
        )
    )
    await session.flush()
