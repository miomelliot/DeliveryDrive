from typing import List, Sequence, cast

import httpx

from src.core.config import Settings
from src.schemas.logistics import AddressRead


async def fetch_distance_matrix(
    addresses: Sequence[AddressRead], profile: str, settings: Settings
) -> list[list[float]]:
    coords = ";".join(f"{a.lon},{a.lat}" for a in addresses)
    url = f"{settings.osrm_url.rstrip('/')}/table/v1/{profile}/{coords}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params={"annotations": "distance"})
        resp.raise_for_status()
        data = resp.json()
    return cast(List[List[float]], data.get("distances", []))
