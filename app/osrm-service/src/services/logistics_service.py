from typing import Any, Dict, Generator, List, Sequence, Tuple

from loguru import logger

from src.core.config import Settings
from src.db.graph import get_neo4j_session
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
            if addr.id != payload.warehouse.id:
                yield addr


def _pairs(addr_ids: Sequence[str], matrix: list[list[float]]) -> list[tuple[str, str, float]]:
    rows: list[tuple[str, str, float]] = []
    for i, from_id in enumerate(addr_ids):
        for j, to_id in enumerate(addr_ids):
            if i == j:
                continue
            rows.append((from_id, to_id, float(matrix[i][j])))
    return rows


async def _ensure_distances(
    addresses: List[AddressRead],
    addr_ids: List[str],
    profile: str,
    settings: Settings,
) -> Dict[Tuple[str, str], float]:
    logger.debug(f"Ensuring distances for {len(addr_ids)} addresses")
    async with get_neo4j_session() as session:
        existing = await fetch_distances(session, addr_ids)
        logger.debug(
            f"Found {len(existing)} distances in cache",
        )

        expected = len(addr_ids) * (len(addr_ids) - 1)
        if len(existing) < expected:
            matrix = await fetch_distance_matrix(addresses, profile, settings)
            sample = [row[:3] for row in matrix[:3]]
            logger.debug(
                f"Matrix sample {sample}",
            )

            all_pairs = _pairs(addr_ids, matrix)
            missing_rows = [(f, t, d) for f, t, d in all_pairs if (f, t) not in existing]

            await upsert_distances(session, missing_rows)
            logger.debug(f"Inserted {len(missing_rows)} missing distances")

            for f, t, d in missing_rows:
                existing[(f, t)] = d

        if len(existing) != expected:
            raise ValueError("Distance matrix incomplete")

        return existing


def _build_matrix(
    addr_ids: List[str],
    existing: Dict[Tuple[str, str], float],
) -> List[List[float]]:
    size: int = len(addr_ids)
    logger.debug(f"Building distance matrix {size}x{size}")
    matrix: List[List[float]] = [[0.0 for _ in range(size)] for _ in range(size)]

    for i, from_id in enumerate(addr_ids):
        for j, to_id in enumerate(addr_ids):
            if i == j:
                matrix[i][j] = 0.0
            else:
                matrix[i][j] = existing.get((from_id, to_id), 0.0)

    return matrix


async def process_logistics(payload: Logistics, settings: Settings) -> List[dict[str, Any]]:
    logger.info(f"Processing logistics: {len(payload.orders)} orders, {len(payload.creates)} couriers")
    addresses: List[AddressRead] = [payload.warehouse]
    addresses.extend(list(_distinct_addresses(payload)))

    async with get_neo4j_session() as session:
        await upsert_addresses(session, addresses)
        logger.debug(f"Upserted {len(addresses)} addresses")

    addr_ids: List[str] = [str(a.id) for a in addresses]

    existing = await _ensure_distances(
        addresses=addresses,
        addr_ids=addr_ids,
        profile=payload.osrm_profile,
        settings=settings,
    )

    matrix: List[List[float]] = _build_matrix(addr_ids, existing)
    logger.debug("Distance matrix built")

    routes = solve_vrp(
        matrix,
        payload.orders,
        payload.creates,
        payload.solver,
    )
    logger.info(f"Route solver produced {len(routes)} routes")

    result: List[dict[str, Any]] = []
    for idx, route in enumerate(routes):
        result.append(
            {
                "courier_id": str(payload.creates[idx].courier_id),
                "time_window": [
                    payload.creates[idx].time_window[0].isoformat(),
                    payload.creates[idx].time_window[1].isoformat(),
                ],
                "orders": [str(order_id) for order_id in route],
            }
        )

    return result
