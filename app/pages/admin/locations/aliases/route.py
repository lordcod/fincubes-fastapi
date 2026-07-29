from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.errors import APIError, ErrorCode
from app.models.location.location_object import LocationObject
from app.schemas.location.location import (
    LocationAliasesAdd,
    LocationCatalogItem,
    LocationEntitySearchItem,
    LocationObjectCreate,
    LocationObjectOut,
)
from app.services.location_catalog import (
    add_aliases_to_location_object,
    create_location_object,
    find_exact_alias,
    matches_required_location_context,
    search_location_entities,
)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get(
    "/",
    response_model=dict[str, list[LocationCatalogItem]],
)
@require_scope("athlete:read")
async def get_location_catalog(
    region_id: Optional[UUID] = None,
    city_id: Optional[UUID] = None,
):
    rows = await LocationObject.all().order_by("region", "city", "id")
    catalog: dict[str, list[LocationCatalogItem]] = {}
    for row in rows:
        if not matches_required_location_context(
            row,
            region_id=region_id,
            city_id=city_id,
        ):
            continue
        item = LocationCatalogItem(
            id=row.id,
            aliases=row.aliases or [],
            club=row.club,
            club_id=row.club_id,
            city=row.city,
            city_id=row.city_id,
            region=row.region,
            region_id=row.region_id,
            required=sorted(row.required or []),
        )
        for alias in row.aliases or []:
            catalog.setdefault(alias, []).append(item)
    return dict(sorted(catalog.items()))


@router.get("/resolve", response_model=LocationObjectOut)
@require_scope("athlete:read")
async def resolve_location_alias(
    alias: str = Query(min_length=1),
    region_id: Optional[UUID] = None,
):
    location = await find_exact_alias(alias, region_id=region_id)
    if location is None:
        raise APIError(ErrorCode.LOCATION_ALIAS_NOT_FOUND)
    return location


@router.get("/search", response_model=list[LocationEntitySearchItem])
@require_scope("athlete:read")
async def search_aliases(
    query: str = Query(min_length=1),
    region_id: Optional[UUID] = None,
    city_id: Optional[UUID] = None,
    limit: int = Query(default=10, ge=1, le=50),
):
    return await search_location_entities(
        "alias",
        query,
        limit=limit,
        region_id=region_id,
        city_id=city_id,
    )


@router.post(
    "/",
    response_model=LocationObjectOut,
    status_code=status.HTTP_201_CREATED,
)
@require_scope("athlete:create")
async def add_location_object(payload: LocationObjectCreate):
    return await create_location_object(payload)


@router.post(
    "/{location_id}/aliases/",
    response_model=LocationObjectOut,
)
@require_scope("athlete:create")
async def add_location_aliases(
    location_id: UUID,
    payload: LocationAliasesAdd,
):
    return await add_aliases_to_location_object(
        location_id,
        payload.aliases,
    )
