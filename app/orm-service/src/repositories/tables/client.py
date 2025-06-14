# src/repositories/tables/client.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address, Client
from src.repositories.tables.address import AddressRepository
from src.repositories.tables.base import CRUDRepository
from src.schemas.client import ClientCreate, ClientUpdate
from src.schemas.order import OrderCreateAPI


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
