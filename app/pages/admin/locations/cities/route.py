from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.location.location import LocationEntitySearchItem
from app.services.location_catalog import search_location_entities
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=list[LocationEntitySearchItem])
@require_scope("athlete:read")
async def search_cities(
    query: str = Query(min_length=1),
    region: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=50),
):
    return await search_location_entities(
        "city",
        query,
        limit=limit,
        region=region,
    )
