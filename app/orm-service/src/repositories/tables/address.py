# src/repositories/tables/address.py


import asyncio
from typing import Any, Final
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address
from src.repositories.tables.base import CRUDRepository
from src.schemas.address import AddressCreate, AddressUpdate, AddressUpdateAPI
from src.schemas.order import OrderCreateAPI
from src.schemas.warehouse import WarehouseCreateAPI
from src.utils.http_error import BadRequestError, NotFoundError

_LOCAL_NOMINATIM_URL: Final[str] = "http://localhost:7070/search"
_PUBLIC_NOMINATIM_URL: Final[str] = "https://nominatim.openstreetmap.org/search"
_HTTP_TIMEOUT = httpx.Timeout(10)  # сек

HEADERS: dict[str, str] = {"User-Agent": "DeliveryDrive/0.1 (https://github.com/miomelliot/DeliveryDrive)"}


class AddressRepository(CRUDRepository[Address, AddressCreate, AddressUpdate]):
    def __init__(self) -> None:
        super().__init__(Address)

    async def create_raw(self, session: AsyncSession, raw_data: OrderCreateAPI | WarehouseCreateAPI) -> Address:
        city, street, building = self._parse_location(raw_data.location)
        lat, lon = await self._geocode(raw_data.location)

        obj_in = AddressCreate(
            city=city,
            street=street,
            building=building,
            lat=lat,
            lon=lon,
        )
        return await super().create(session, obj_in)

    async def update_by_id_raw(self, session: AsyncSession, id: UUID, address_raw: AddressUpdateAPI) -> Address:
        city, street, building = self._parse_location(address_raw.location)
        lat, lon = await self._geocode(address_raw.location)
        obj_in = AddressUpdate(
            city=city,
            street=street,
            building=building,
            lat=lat,
            lon=lon,
        )
        return await super().update_by_id(session, id, obj_in)

    @staticmethod
    def _parse_location(location: str | None) -> tuple[str, str | None, str]:
        if location is None:
            raise BadRequestError("Ошибка адреса: допустимый формат «Город, Улица, Дом» или «Город, Дом»")
        parts: list[str] = [p.strip() for p in location.split(",")]
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            return parts[0], None, parts[1]
        raise BadRequestError("Ошибка адреса: допустимый формат «Город, Улица, Дом» или «Город, Дом»")

    @staticmethod
    async def _geocode(location: str | None) -> tuple[float, float]:
        """
        1. Проверяем формат (Город, Улица, Дом | Город, Дом)
        2. Пробуем локальный Nominatim
        3. При неуспехе — публичный Nominatim (с паузой 1 с)
        4. Если тоже пусто — NotFoundError
        """
        if location is None:
            raise BadRequestError("Ошибка адреса: допустимый формат «Город, Улица, Дом» или «Город, Дом»")
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
        try:
            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, headers=HEADERS) as client:
                resp: httpx.Response = await client.get(url, params=params)
                if resp.status_code != 200:
                    return None
                data = resp.json()
                if not data:
                    return None
                return float(data[0]["lat"]), float(data[0]["lon"])
        except httpx.HTTPError:
            return None
