# src/services/geocoder.py
from pydantic import BaseModel


class GeocodeRequest(BaseModel):
    address: str


class GeocodeResponse(BaseModel):
    lat: float
    lon: float
    display_name: str
