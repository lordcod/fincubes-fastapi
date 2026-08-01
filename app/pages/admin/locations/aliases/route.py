from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.core.errors import APIError, ErrorCode
from app.models.location.location_alias import LocationAlias
from app.schemas.location.location import (
    LocationAliasOut,
    LocationAliasesAdd,
    LocationAliasUpdate,
    LocationCatalogItem,
    LocationEntitySearchItem,
    LocationMergePreview,
    LocationMergeRequest,
    LocationMergeResult,
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
    location_object_out,
    merge_location_object,
    matches_required_location_context,
    preview_location_merge,
    resolve_location_alias as resolve_location_alias_service,
    search_location_entities,
    update_location_alias,
    update_location_object,
)
from app.shared.utils.location_text import normalize_location_text
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


def _matches_required_filter(alias_required: list[str], value: str) -> bool:
    normalized = normalize_location_text(value)
    required_fields = set(alias_required or [])
    if normalized in {"true", "1", "yes"}:
        return bool(required_fields)
    if normalized in {"false", "0", "no"}:
        return not required_fields
    requested = {
        item.strip()
        for item in normalized.split(",")
        if item.strip()
    }
    return requested <= required_fields


def _matches_location_catalog_query(
    alias_rule: LocationAlias,
    query: str,
    kind: Optional[Literal["regions", "cities", "clubs"]],
) -> bool:
    query_key = normalize_location_text(query)
    location = alias_rule.location_object
    if kind == "regions":
        values = [location.region]
    elif kind == "cities":
        values = [location.city]
    elif kind == "clubs":
        values = [location.club]
    else:
        values = [alias_rule.alias, location.club, location.city, location.region]
    return any(
        query_key in normalize_location_text(value)
        for value in values
        if value
    )


def _sort_location_catalog(
    catalog: dict[str, list[LocationCatalogItem]],
    sort: str,
) -> dict[str, list[LocationCatalogItem]]:
    reverse = sort.startswith("-")
    field = sort.removeprefix("-")

    def item_key(alias: str) -> str:
        first = catalog[alias][0]
        value = alias if field == "alias" else getattr(first, field) or ""
        return normalize_location_text(value)

    return {
        alias: catalog[alias]
        for alias in sorted(catalog, key=item_key, reverse=reverse)
    }


@router.get(
    "/",
    response_model=dict[str, list[LocationCatalogItem]],
)
@require_scope("athlete:read")
async def get_location_catalog(
    region: Optional[str] = None,
    city: Optional[str] = None,
    query: Optional[str] = None,
    kind: Optional[Literal["regions", "cities", "clubs"]] = None,
    required: Optional[str] = None,
    sort: Literal["alias", "-alias", "region", "-region", "city", "-city", "club", "-club"] = "alias",
):
    rows = await LocationAlias.all().prefetch_related("location_object")
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
        if required is not None and not _matches_required_filter(row.required or [], required):
            continue
        if query and not _matches_location_catalog_query(row, query, kind):
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
    return _sort_location_catalog(catalog, sort)


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
    return await location_object_out(location)


@router.get(
    "/{source_location_id}/merge-preview/",
    response_model=LocationMergePreview,
)
@require_scope("athlete:read")
async def preview_location_object_merge(
    source_location_id: UUID,
    target_location_id: UUID,
):
    return await preview_location_merge(source_location_id, target_location_id)


@router.post(
    "/{source_location_id}/merge/",
    response_model=LocationMergeResult,
)
@require_scope("athlete:write")
async def merge_location_object_route(
    source_location_id: UUID,
    payload: LocationMergeRequest,
):
    return await merge_location_object(source_location_id, payload)


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
    return await location_object_out(location)


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
    return await location_object_out(location)


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
