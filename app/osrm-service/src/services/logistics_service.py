from typing import Any, Generator

from neo4j import AsyncSession

from src.repositories.neo4j.address import upsert_addresses
from src.schemas.logistics import AddressRead, Logistics


def _distinct_addresses(payload: Logistics) -> Generator[AddressRead, Any, None]:
    seen: set[str] = set()
    for order in payload.orders:
        addr: AddressRead = order.address
        if addr.id not in seen:
            seen.add(str(addr.id))
            yield addr


async def ingest_addresses(payload: Logistics, neo4j: AsyncSession) -> None:
    addresses: list[AddressRead] = list(_distinct_addresses(payload))
    await upsert_addresses(neo4j, addresses)
