from time import perf_counter
from typing import List, Sequence, cast

import httpx
from loguru import logger

from src.core.config import Settings
from src.schemas.logistics import AddressRead


async def fetch_distance_matrix(
    addresses: Sequence[AddressRead], profile: str, settings: Settings
) -> list[list[float]]:
    coords: str = ";".join(f"{a.lon},{a.lat}" for a in addresses)
    url: str = f"{settings.osrm_url.rstrip('/')}/table/v1/{profile}/{coords}"
    logger.debug("Requesting OSRM matrix: %s", url)
    start = perf_counter()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp: httpx.Response = await client.get(url, params={"annotations": "distance"})
    resp.raise_for_status()
    duration = perf_counter() - start
    logger.debug("OSRM response received in %.2f sec", duration)
    data = resp.json()
    return cast(List[List[float]], data.get("distances", []))
