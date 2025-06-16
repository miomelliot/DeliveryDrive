"""Utilities for persisting planned routes."""

from __future__ import annotations

from datetime import date, datetime, timezone
from datetime import time as dt_time
from typing import Sequence
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Order, Route, RouteItem, Tracking
from src.repositories.tables.order_status import OrderStatusRepository


async def save_routes(
    session: AsyncSession,
    plans: Sequence[dict[str, object]],
) -> list[Route]:
    """Persist routes and create tracking records."""

    scheduled_id: int = await OrderStatusRepository().get_code_id(session, "scheduled")
    created: list[Route] = []
    now: datetime = datetime.now(timezone.utc)

    for plan in plans:
        courier_id = UUID(str(plan["courier_id"]))
        tw_start_str, tw_end_str = plan.get("time_window", [None, None])  # type: ignore
        tw_start = (
            dt_time.fromisoformat(tw_start_str) if tw_start_str else now.time()  # type: ignore
        )
        tw_end = (
            dt_time.fromisoformat(tw_end_str) if tw_end_str else now.time()  # type: ignore
        )

        route = Route(
            courier_id=courier_id,
            date=date.today(),
            planned_start=datetime.combine(date.today(), tw_start, tzinfo=timezone.utc),
            planned_end=datetime.combine(date.today(), tw_end, tzinfo=timezone.utc),
        )
        session.add(route)
        await session.flush()

        order_ids: list[UUID] = [UUID(o) for o in plan.get("orders", [])]  # type: ignore
        for seq, oid in enumerate(order_ids):
            item = RouteItem(route_id=route.id, order_id=oid, sequence=seq)
            session.add(item)
            await session.flush()

            session.add(
                Tracking(
                    route_item_id=item.id,
                    event_type_id=1,
                    event_time=now,
                )
            )

        if order_ids:
            await session.execute(update(Order).where(Order.id.in_(order_ids)).values(status_id=scheduled_id))

        created.append(route)

    return created
