from time import perf_counter
from typing import List, Sequence, cast

import httpx
from loguru import logger

from src.core.config import Settings
from src.schemas.logistics import AddressRead


async def fetch_distance_matrix(
    addresses: Sequence[AddressRead], profile: str, settings: Settings
) -> list[list[float]]:
    """Fetch full distance matrix for the given addresses.

    The OSRM table service has a hard limit on the number of coordinates per
    request, therefore batches of more than 100 points are sliced and the
    resulting matrices are merged together.
    """

    coords_all: list[str] = [f"{a.lon},{a.lat}" for a in addresses]
    n: int = len(coords_all)
    matrix: list[list[float]] = [[0.0 for _ in range(n)] for _ in range(n)]

    chunk: int = 50
    start_total = perf_counter()
    async with httpx.AsyncClient(timeout=300.0) as client:
        for i in range(0, n, chunk):
            for j in range(0, n, chunk):
                src_idx = list(range(i, min(i + chunk, n)))
                dst_idx = list(range(j, min(j + chunk, n)))

                coord_subset = [coords_all[k] for k in src_idx + dst_idx]
                coord_str = ";".join(coord_subset)
                url = f"{settings.osrm_url.rstrip('/')}/table/v1/{profile}/{coord_str}"

                params = {
                    "sources": ";".join(str(k) for k in range(len(src_idx))),
                    "destinations": ";".join(str(len(src_idx) + k) for k in range(len(dst_idx))),
                    "annotations": "distance",
                }
                logger.debug("Requesting OSRM matrix: %s", url)
                start = perf_counter()
                resp: httpx.Response = await client.get(url, params=params)
                resp.raise_for_status()
                duration = perf_counter() - start
                logger.debug("OSRM response received in %.2f sec", duration)

                data = resp.json()
                distances = cast(List[List[float]], data.get("distances", []))
                for ii, s in enumerate(src_idx):
                    for jj, d in enumerate(dst_idx):
                        matrix[s][d] = distances[ii][jj]

    duration_total = perf_counter() - start_total
    logger.debug(f"Total OSRM time {duration_total:2f} sec for {n} addresses")
    return matrix
