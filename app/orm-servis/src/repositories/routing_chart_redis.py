# src/repositories/routing_chart_redis.py
from typing import Awaitable, Set, cast
from uuid import UUID

import redis.asyncio as redis

ONE_HOUR = 60 * 60


class RoutingChartRedis:
    def __init__(self, client: redis.Redis) -> None:
        self.redis: redis.Redis = client

    @staticmethod
    def _key(user_id: UUID) -> str:
        return f"routing_selection:{user_id}"

    # ---------- CRUD ----------
    async def add(self, user_id: UUID, order_id: UUID) -> None:
        key: str = self._key(user_id)

        await cast(Awaitable[int], self.redis.sadd(key, str(order_id)))
        await cast(Awaitable[bool], self.redis.expire(key, ONE_HOUR, nx=True))

    async def remove(self, user_id: UUID, order_id: UUID) -> None:
        await cast(Awaitable[int], self.redis.srem(self._key(user_id), str(order_id)))

    async def list_ids(self, user_id: UUID) -> list[UUID]:
        raw: Set[str] = await cast(
            Awaitable[Set[str]],
            self.redis.smembers(self._key(user_id)),
        )
        return [UUID(v) for v in raw]

    async def clear(self, user_id: UUID) -> None:
        await cast(Awaitable[int], self.redis.delete(self._key(user_id)))
