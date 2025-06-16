from typing import Sequence

from neo4j import AsyncSession

from src.schemas.logistics import AddressRead

# Один запрос UNWIND-ом на пачку адресов
_CYPHER = """
UNWIND $rows AS row
MERGE (a:Address {id: row.id})
ON CREATE SET
    a.city     = row.city,
    a.street   = row.street,
    a.building = row.building,
    a.lat      = row.lat,
    a.lon      = row.lon
"""


def _row(a: AddressRead) -> dict[str, str | float]:
    return {
        "id": str(a.id),
        "city": a.city,
        "street": a.street or "",
        "building": a.building,
        "lat": a.lat,
        "lon": a.lon,
    }


async def upsert_addresses(session: AsyncSession, addresses: Sequence[AddressRead]) -> None:
    if not addresses:
        return
    rows: list[dict[str, str | float]] = [_row(a) for a in addresses]
    await session.run(_CYPHER, rows=rows)
