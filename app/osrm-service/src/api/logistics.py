from fastapi import APIRouter, Depends, status
from neo4j import AsyncSession

from src.dependencies.db import neo4j_session
from src.schemas.logistics import Logistics
from src.services.logistics_service import ingest_addresses

router = APIRouter(prefix="/logistics", tags=["Logistics"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def upload_logistics(
    payload: Logistics,
    neo4j: AsyncSession = Depends(neo4j_session),
) -> dict[str, str]:
    await ingest_addresses(payload, neo4j)
    return {"detail": f"{len(payload.orders)} orders accepted"}
