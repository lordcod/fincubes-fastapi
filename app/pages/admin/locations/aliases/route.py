from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.core.errors import APIError, ErrorCode
from app.models.location.location_alias import LocationAlias
from app.models.location.location_object import LocationObject
from app.schemas.location.location import (
    LocationAliasOut,
    LocationAliasesAdd,
    LocationAliasUpdate,
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
    delete_location_alias,
    matches_required_location_context,
    resolve_location_alias as resolve_location_alias_service,
    search_location_entities,
    update_location_alias,
    update_location_object,
)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


async def _location_object_out(location: LocationObject) -> LocationObjectOut:
    aliases = await LocationAlias.filter(location_object=location).order_by("alias")
    return LocationObjectOut(
        id=location.id,
        club=location.club,
        city=location.city,
        region=location.region,
        aliases=[
            LocationAliasOut(
                id=alias.id,
                location_object_id=location.id,
                alias=alias.alias,
                required=sorted(alias.required or []),
            )
            for alias in aliases
        ],
    )


@router.get(
    "/",
    response_model=dict[str, list[LocationCatalogItem]],
)
@require_scope("athlete:read")
async def get_location_catalog(
    region: Optional[str] = None,
    city: Optional[str] = None,
):
    rows = await LocationAlias.all().prefetch_related("location_object").order_by("alias")
    catalog: dict[str, list[LocationCatalogItem]] = {}
    for row in rows:
        location = row.location_object
        if (region or city) and not matches_required_location_context(
            location,
            region=region,
            city=city,
            required=row.required,
        ):
            continue
        item = LocationCatalogItem(
            id=location.id,
            alias_id=row.id,
            alias=row.alias,
            club=location.club,
            city=location.city,
            region=location.region,
            required=sorted(row.required or []),
        )
        catalog.setdefault(row.alias, []).append(item)
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
    location = await create_location_object(payload)
    return await _location_object_out(location)


@router.patch(
    "/{location_id}/",
    response_model=LocationObjectOut,
)
@require_scope("athlete:write")
async def edit_location_object(
    location_id: UUID,
    payload: LocationObjectUpdate,
):
    location = await update_location_object(location_id, payload)
    return await _location_object_out(location)


@router.post(
    "/{location_id}/aliases/",
    response_model=LocationObjectOut,
)
@require_scope("athlete:create")
async def add_location_aliases(
    location_id: UUID,
    payload: LocationAliasesAdd,
):
    location = await add_aliases_to_location_object(
        location_id,
        payload.aliases,
        payload.required,
    )
    return await _location_object_out(location)


@router.patch(
    "/alias/{alias_id}/",
    response_model=LocationAliasOut,
)
@require_scope("athlete:write")
async def edit_location_alias(
    alias_id: UUID,
    payload: LocationAliasUpdate,
):
    alias_rule = await update_location_alias(alias_id, payload)
    return LocationAliasOut(
        id=alias_rule.id,
        location_object_id=alias_rule.location_object_id,
        alias=alias_rule.alias,
        required=sorted(alias_rule.required or []),
    )


@router.delete(
    "/alias/{alias_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
)
@require_scope("athlete:write")
async def remove_location_alias(alias_id: UUID):
    await delete_location_alias(alias_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
