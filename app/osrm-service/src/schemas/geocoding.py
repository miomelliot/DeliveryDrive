# src/schemas/geocoding.py
from urllib.parse import quote_plus

import httpx

from src.services.geocoder import GeocodeRequest, GeocodeResponse


class Geocoder:
    def __init__(self) -> None:
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers: dict[str, str] = {"User-Agent": "DeliveryDrive/0.1 (https://github.com/miomelliot/DeliveryDrive)"}

    async def geocode(self, query: GeocodeRequest) -> GeocodeResponse:
        encoded: str = quote_plus(query.address)
        url: str = f"{self.base_url}?format=json&q={encoded}"

        async with httpx.AsyncClient() as client:
            resp: httpx.Response = await client.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()

        if not data:
            raise ValueError("Address not found")

        first = data[0]
        return GeocodeResponse(lat=float(first["lat"]), lon=float(first["lon"]), display_name=first["display_name"])
