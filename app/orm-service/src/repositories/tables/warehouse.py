# src/repositories/tables/warehouse.py
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Address, Warehouse
from src.repositories.tables.address import AddressRepository
from src.repositories.tables.base import CRUDRepository
from src.schemas.warehouse import WarehouseCreate, WarehouseCreateAPI, WarehouseUpdate


class WarehouseRepository(CRUDRepository[Warehouse, WarehouseCreate, WarehouseUpdate]):
    def __init__(self) -> None:
        super().__init__(Warehouse)

    async def create_raw(self, session: AsyncSession, raw_data: WarehouseCreateAPI) -> Warehouse:
        address: Address = await AddressRepository().create_raw(session, raw_data)

        obj_in = WarehouseCreate(address_id=address.id)
        warehouse: Sequence[Warehouse] = await super().list(session)
        if warehouse:
            return await super().update_by_id(session, warehouse[0].id, WarehouseUpdate(address_id=address.id))
        return await super().create(session, obj_in)
