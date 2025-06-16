import os
import sys
from uuid import uuid4
from typing import List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

from src.schemas.logistics import AddressRead
from src.services import logistics_service


@pytest.mark.asyncio
async def test_ensure_distances_inserts_all(monkeypatch):
    addresses: List[AddressRead] = [
        AddressRead(id=uuid4(), city="c", street="s", building="b", lat=i, lon=i)
        for i in range(10)
    ]
    addr_ids = [str(a.id) for a in addresses]
    fake_store: dict[tuple[str, str], float] = {}

    async def fake_fetch_distances(session, ids):
        return {k: v for k, v in fake_store.items() if k[0] in ids and k[1] in ids}

    async def fake_upsert_distances(session, rows):
        for f, t, d in rows:
            fake_store[(f, t)] = d

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def fake_get_session():
        yield None

    async def fake_fetch_matrix(addresses, profile, settings):
        n = len(addresses)
        return [[float(i * n + j) for j in range(n)] for i in range(n)]

    monkeypatch.setattr(logistics_service, "fetch_distances", fake_fetch_distances)
    monkeypatch.setattr(logistics_service, "upsert_distances", fake_upsert_distances)
    monkeypatch.setattr(logistics_service, "get_neo4j_session", fake_get_session)
    monkeypatch.setattr(logistics_service, "fetch_distance_matrix", fake_fetch_matrix)

    settings = logistics_service.Settings()
    result = await logistics_service._ensure_distances(addresses, addr_ids, "driving", settings)
    assert len(fake_store) == 90
    assert len(result) == 90
