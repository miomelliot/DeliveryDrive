# src/services/route_service.py
from datetime import date, datetime, timezone
from datetime import time as dt_time
from typing import Sequence
from uuid import UUID

from loguru import logger
from sqlalchemy import Result, Select, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Notification,
    Order,
    OrderStatus,
    Role,
    Route,
    RouteItem,
    Tracking,
    User,
)


async def _get_status_id(session: AsyncSession, code: str) -> int:
    stmt: Select[tuple[int]] = select(OrderStatus.id).where(OrderStatus.code == code)
    res: Result[tuple[int]] = await session.execute(stmt)
    status_id: int | None = res.scalars().first()
    if status_id is None:
        raise ValueError(f"Status with code '{code}' not found")
    return status_id


async def _get_manager_ids(session: AsyncSession) -> list[UUID]:
    stmt: Select[tuple[UUID]] = select(User.id).join(Role, User.role_id == Role.id).where(Role.name == "manager")
    res: Result[tuple[UUID]] = await session.execute(stmt)
    return list(res.scalars())


async def _create_notifications(session: AsyncSession, user_ids: Sequence[UUID], text: str) -> None:
    session.add_all([Notification(user_id=uid, text=text) for uid in user_ids])
    await session.flush()


async def save_routes(
    session: AsyncSession,
    plans: Sequence[dict[str, object]],
) -> list[Route]:
    logger.info(f"Saving {len(plans)} planned routes")
    scheduled_id: int = await _get_status_id(session, "scheduled")
    created: list[Route] = []
    now: datetime = datetime.now(timezone.utc)
    manager_ids: list[UUID] = await _get_manager_ids(session)

    for plan in plans:
        courier_id = UUID(str(plan["courier_id"]))
        tw_start_str, tw_end_str = plan.get("time_window", [None, None])  # type: ignore
        tw_start = (
            dt_time.fromisoformat(tw_start_str) if tw_start_str else now.time()  # type: ignore
        )
        tw_end = (
            dt_time.fromisoformat(tw_end_str) if tw_end_str else now.time()  # type: ignore
        )

        order_ids: list[UUID] = [UUID(o) for o in plan.get("orders", [])]  # type: ignore
        logger.debug(f"Creating route for courier {courier_id} with {len(order_ids)} orders")
        route = Route(
            courier_id=courier_id,
            date=date.today(),
            planned_start=datetime.combine(date.today(), tw_start, tzinfo=timezone.utc),
            planned_end=datetime.combine(date.today(), tw_end, tzinfo=timezone.utc),
        )
        session.add(route)
        await session.flush()
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

        await _create_notifications(
            session,
            [*manager_ids, courier_id],
            "Создан новый маршрут",
        )

        created.append(route)

    logger.info(f"{len(created)} routes saved")

    return created
