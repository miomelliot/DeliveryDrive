# src/repositories/tables/address.py
from __future__ import annotations

import asyncio
from typing import Any, Final

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address
from src.repositories.tables.base import CRUDRepository
from src.schemas.address import AddressCreate, AddressUpdate
from src.utils.http_error import BadRequestError, NotFoundError

_LOCAL_NOMINATIM_URL: Final[str] = "http://nominatim:8080/search"
_PUBLIC_NOMINATIM_URL: Final[str] = "https://nominatim.openstreetmap.org/search"
_HTTP_TIMEOUT = httpx.Timeout(10)  # сек

HEADERS: dict[str, str] = {"User-Agent": "DeliveryDrive/0.1 (https://github.com/miomelliot/DeliveryDrive)"}


class AddressRepository(CRUDRepository[Address, AddressCreate, AddressUpdate]):
    def __init__(self) -> None:
        super().__init__(Address)

    async def create(self, session: AsyncSession, obj_in: AddressCreate) -> Address:
        if obj_in.lat is None or obj_in.lon is None:
            lat, lon = await self._geocode(obj_in.lon)
            obj_in.lat = lat
            obj_in.lon = lon

        return await super().create(session, obj_in)

    @staticmethod
    async def _geocode(location: str) -> tuple[float, float]:
        """
        1. Проверяем формат (Город, Улица, Дом | Город, Дом)
        2. Пробуем локальный Nominatim
        3. При неуспехе — публичный Nominatim (с паузой 1 с)
        4. Если тоже пусто — NotFoundError
        """
        parts: list[str] = [p.strip() for p in location.split(",")]
        if len(parts) not in (2, 3):
            raise BadRequestError("Ошибка адреса: допустимый формат «Город, Улица, Дом» или «Город, Дом»")

        params = {"q": location, "format": "json", "limit": 1}

        coords: tuple[float, float] | None = await AddressRepository._fetch_coords(_LOCAL_NOMINATIM_URL, params)
        if coords:
            return coords

        await asyncio.sleep(1)  # TOS: не >1 req/сек
        coords = await AddressRepository._fetch_coords(_PUBLIC_NOMINATIM_URL, params)
        if coords:
            return coords

        raise NotFoundError("Адрес не найден")

    @staticmethod
    async def _fetch_coords(url: str, params: dict[str, Any]) -> tuple[float, float] | None:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, headers=HEADERS) as client:
            resp: httpx.Response = await client.get(url, params=params)
            if resp.status_code != 200:
                return None
            data = resp.json()
            if not data:
                return None
            return float(data[0]["lat"]), float(data[0]["lon"])
