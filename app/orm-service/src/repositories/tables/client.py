# src/repositories/tables/client.py
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Client
from src.repositories.tables.base import CRUDRepository
from src.schemas.client import ClientCreate, ClientUpdate


class ClientRepository(CRUDRepository[Client, ClientCreate, ClientUpdate]):
    def __init__(self) -> None:
        super().__init__(Client)

    async def create(self, session: AsyncSession, obj_in: ClientCreate) -> Client:
        return await super().create(session, obj_in)
