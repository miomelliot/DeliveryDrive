# src/repositories/tables/client.py
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address, Client
from src.repositories.tables.address import AddressRepository
from src.repositories.tables.base import CRUDRepository
from src.schemas.address import AddressUpdateAPI
from src.schemas.client import ClientCreate, ClientUpdate
from src.schemas.order import OrderCreateAPI
from src.schemas.order_detail_read import OrderDetailUpdate


class ClientRepository(CRUDRepository[Client, ClientCreate, ClientUpdate]):
    def __init__(self) -> None:
        super().__init__(Client)

    async def create_raw(self, session: AsyncSession, raw_data: OrderCreateAPI) -> Client:
        address: Address = await AddressRepository().create_raw(session, raw_data)
        obj_in = ClientCreate(
            name=raw_data.name,
            phone=raw_data.phone,
            address_id=address.id,
        )

        return await super().create(session, obj_in)

    async def update_raw(
        self,
        session: AsyncSession,
        client_id: UUID,
        raw: OrderDetailUpdate,
    ) -> Client:
        kwargs: dict[str, Any] = {}

        if raw.location is not None:
            addr_update = AddressUpdateAPI(location=raw.location)
            address: Address = await AddressRepository().update_by_id_raw(session, client_id, addr_update)
            kwargs["address_id"] = address.id

        if raw.phone is not None:
            kwargs["phone"] = raw.phone
        if raw.client_name is not None:
            kwargs["name"] = raw.client_name

        if not kwargs:
            return await self.get(session, client_id)

        obj_in = ClientUpdate(**kwargs)
        return await super().update_by_id(session, client_id, obj_in)
