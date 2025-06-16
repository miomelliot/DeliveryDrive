from typing import Any, Dict, Sequence, Tuple

from neo4j import AsyncResult, AsyncSession

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


_SELECT_DISTANCES = """
MATCH (a:Address)-[r:DISTANCE]->(b:Address)
WHERE a.id IN $ids AND b.id IN $ids
RETURN a.id AS from_id, b.id AS to_id, r.value AS distance
"""


async def fetch_distances(session: AsyncSession, ids: Sequence[str]) -> Dict[Tuple[str, str], float]:
    result: AsyncResult = await session.run(_SELECT_DISTANCES, ids=list(ids))
    records: list[list[Any]] = await result.values("from_id", "to_id", "distance")
    return {(f, t): float(d) for f, t, d in records}


_UPSERT_DISTANCES = """
UNWIND $rows AS row
MATCH (a:Address {id: row.from})
MATCH (b:Address {id: row.to})
MERGE (a)-[r:DISTANCE]->(b)
SET r.value = row.distance
"""


async def upsert_distances(session: AsyncSession, rows: Sequence[Tuple[str, str, float]]) -> None:
    if not rows:
        return
    payload = [{"from": f, "to": t, "distance": d} for f, t, d in rows]
    await session.run(_UPSERT_DISTANCES, rows=payload)
