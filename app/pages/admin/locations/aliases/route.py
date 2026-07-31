from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.errors import APIError, ErrorCode
from app.models.location.location_object import LocationObject
from app.schemas.location.location import (
    LocationAliasesAdd,
    LocationCatalogItem,
    LocationEntitySearchItem,
    LocationObjectCreate,
    LocationObjectOut,
    LocationObjectUpdate,
    LocationResolveRequest,
    LocationResolveResult,
)
from app.services.location_catalog import (
    add_aliases_to_location_object,
    create_location_object,
    matches_required_location_context,
    resolve_location_alias as resolve_location_alias_service,
    search_location_entities,
    update_location_object,
)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get(
    "/",
    response_model=dict[str, list[LocationCatalogItem]],
)
@require_scope("athlete:read")
async def get_location_catalog(
    region: Optional[str] = None,
    city: Optional[str] = None,
):
    rows = await LocationObject.all().order_by("region", "city", "id")
    catalog: dict[str, list[LocationCatalogItem]] = {}
    for row in rows:
        if (region or city) and not matches_required_location_context(
            row,
            region=region,
            city=city,
        ):
            continue
        item = LocationCatalogItem(
            id=row.id,
            aliases=row.aliases or [],
            club=row.club,
            city=row.city,
            region=row.region,
            required=sorted(row.required or []),
        )
        for alias in row.aliases or []:
            catalog.setdefault(alias, []).append(item)
    return dict(sorted(catalog.items()))


@router.get("/resolve", response_model=LocationResolveResult)
@require_scope("athlete:read")
async def resolve_location_alias(
    alias: str = Query(min_length=1),
    city: Optional[str] = None,
    region: Optional[str] = None,
):
    resolved = await resolve_location_alias_service(
        LocationResolveRequest(alias=alias, city=city, region=region)
    )
    if resolved is None:
        raise APIError(ErrorCode.LOCATION_ALIAS_NOT_FOUND)
    return resolved


@router.get("/search", response_model=list[LocationEntitySearchItem])
@require_scope("athlete:read")
async def search_aliases(
    query: str = Query(min_length=1),
    region: Optional[str] = None,
    city: Optional[str] = None,
    limit: int = Query(default=10, ge=1, le=50),
):
    return await search_location_entities(
        "alias",
        query,
        limit=limit,
        region=region,
        city=city,
    )


@router.post(
    "/",
    response_model=LocationObjectOut,
    status_code=status.HTTP_201_CREATED,
)
@require_scope("athlete:create")
async def add_location_object(payload: LocationObjectCreate):
    return await create_location_object(payload)


@router.patch(
    "/{location_id}/",
    response_model=LocationObjectOut,
)
@require_scope("athlete:write")
async def edit_location_object(
    location_id: UUID,
    payload: LocationObjectUpdate,
):
    return await update_location_object(location_id, payload)


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
