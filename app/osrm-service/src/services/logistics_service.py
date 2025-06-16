from typing import Any, Dict, Generator, List, Tuple

from neo4j import AsyncSession

from src.core.config import Settings
from src.repositories.neo4j.address import (
    fetch_distances,
    upsert_addresses,
    upsert_distances,
)
from src.schemas.logistics import AddressRead, Logistics
from src.services.osrm_client import fetch_distance_matrix
from src.services.route_solver import solve_vrp


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


async def _ensure_distances(
    addresses: List[AddressRead],
    addr_ids: List[str],
    neo4j: AsyncSession,
    profile: str,
    settings: Settings,
) -> Dict[Tuple[str, str], float]:
    existing: Dict[Tuple[str, str], float] = await fetch_distances(neo4j, addr_ids)
    if len(existing) < len(addr_ids) * len(addr_ids):
        matrix: List[List[float]] = await fetch_distance_matrix(addresses, profile, settings)
        missing_rows: List[Tuple[str, str, float]] = []
        for i, from_id in enumerate(addr_ids):
            for j, to_id in enumerate(addr_ids):
                if i == j:
                    continue
                key = (from_id, to_id)
                dist: float = float(matrix[i][j]) if matrix else 0.0
                if key not in existing:
                    missing_rows.append((from_id, to_id, dist))
                    existing[key] = dist
        await upsert_distances(neo4j, missing_rows)
    return existing


def _build_matrix(addr_ids: List[str], existing: Dict[Tuple[str, str], float]) -> List[List[float]]:
    size: int = len(addr_ids)
    matrix: List[List[float]] = [[0.0 for _ in range(size + 1)] for _ in range(size + 1)]
    for i, from_id in enumerate(addr_ids, start=1):
        for j, to_id in enumerate(addr_ids, start=1):
            if i == j:
                matrix[i][j] = 0.0
            else:
                matrix[i][j] = existing.get((from_id, to_id), 0.0)
    return matrix


async def process_logistics(payload: Logistics, neo4j: AsyncSession, settings: Settings) -> List[List[str]]:
    addresses: List[AddressRead] = list(_distinct_addresses(payload))
    await upsert_addresses(neo4j, addresses)

    addr_ids: List[str] = [str(a.id) for a in addresses]
    existing: Dict[Tuple[str, str], float] = await _ensure_distances(
        addresses, addr_ids, neo4j, payload.osrm_profile, settings
    )
    distance_matrix: List[List[float]] = _build_matrix(addr_ids, existing)

    routes_uuid: List[List[str]] = [
        [str(oid) for oid in route]
        for route in solve_vrp(
            distance_matrix,
            payload.orders,
            payload.creates,
            payload.solver,
        )
    ]
    return routes_uuid
