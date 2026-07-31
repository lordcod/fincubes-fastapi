import re
import unicodedata
from typing import Literal, Optional
from uuid import UUID

from app.core.errors import APIError, ErrorCode
from app.models.location.location_object import LocationObject
from app.schemas.location.location import (
    LocationEntitySearchItem,
    LocationObjectCreate,
    LocationResolveRequest,
    LocationResolveResult,
)

LocationEntity = Literal["alias", "club", "city", "region"]


def normalize_location_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    normalized = normalized.replace("ё", "е")
    return re.sub(r"\s+", " ", normalized)


def _matches_text(value: str | None, expected: str | None) -> bool:
    if expected is None:
        return False
    return bool(value) and normalize_location_text(value) == normalize_location_text(expected)


def matches_required_location_context(
    location: LocationObject,
    *,
    region: Optional[str] = None,
    city: Optional[str] = None,
) -> bool:
    required = set(location.required or [])
    if "region" in required and not _matches_text(location.region, region):
        return False
    if "city" in required and not _matches_text(location.city, city):
        return False
    return True


async def find_exact_alias(
    alias: str,
    *,
    region: Optional[str] = None,
    city: Optional[str] = None,
) -> Optional[LocationObject]:
    alias_key = normalize_location_text(alias)
    matches = [
        location
        for location in await LocationObject.all()
        if any(
            normalize_location_text(existing_alias) == alias_key
            for existing_alias in (location.aliases or [])
        )
    ]
    if not matches:
        return None

    contextual_matches = [
        location
        for location in matches
        if matches_required_location_context(location, region=region, city=city)
    ]
    if len(contextual_matches) == 1:
        return contextual_matches[0]
    if len(contextual_matches) > 1:
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)

    if any("city" in set(location.required or []) for location in matches):
        raise APIError(ErrorCode.LOCATION_REGION_REQUIRED)
    if any("region" in set(location.required or []) for location in matches):
        raise APIError(ErrorCode.LOCATION_REGION_REQUIRED)
    if len(matches) > 1:
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)
    return matches[0]


async def resolve_location_alias(
    payload: LocationResolveRequest,
) -> Optional[LocationResolveResult]:
    location = await find_exact_alias(
        payload.alias,
        city=payload.city,
        region=payload.region,
    )
    if location is None:
        return None
    return LocationResolveResult(
        id=location.id,
        alias=payload.alias,
        club=location.club,
        city=location.city,
        region=location.region,
        required=sorted(location.required or []),
    )


async def resolve_athlete_location_fields(
    *,
    alias: Optional[str] = None,
    club: Optional[str],
    city: Optional[str],
    region: Optional[str],
    create_missing_alias: bool = True,
) -> dict[str, Optional[str]]:
    if not alias:
        return {"club": club, "city": city, "region": region}

    resolved = await resolve_location_alias(
        LocationResolveRequest(alias=alias, city=city, region=region)
    )
    if resolved is not None:
        return {
            "club": resolved.club or club,
            "city": resolved.city or city,
            "region": resolved.region or region,
        }

    if not create_missing_alias or not region:
        return {"club": club, "city": city, "region": region}

    location = await create_location_object(
        LocationObjectCreate(
            aliases=[alias],
            club=club,
            city=city,
            region=region,
        )
    )
    return {
        "club": location.club or club,
        "city": location.city or city,
        "region": location.region or region,
    }


def _canonical_identity(location: LocationObject) -> tuple[str, str, str]:
    return (
        normalize_location_text(location.club or ""),
        normalize_location_text(location.city or ""),
        normalize_location_text(location.region),
    )


async def create_location_object(
    payload: LocationObjectCreate,
) -> LocationObject:
    existing_objects = await LocationObject.all()
    incoming_identity = (
        normalize_location_text(payload.club or ""),
        normalize_location_text(payload.city or ""),
        normalize_location_text(payload.region),
    )

    duplicate_aliases: list[str] = []
    for location in existing_objects:
        duplicates = {
            normalize_location_text(alias)
            for alias in payload.aliases
        } & {
            normalize_location_text(alias)
            for alias in (location.aliases or [])
        }
        if not duplicates:
            continue
        if (
            _canonical_identity(location) != incoming_identity
            and not (payload.required and location.required)
        ):
            duplicate_aliases.extend(sorted(duplicates))

    if duplicate_aliases:
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)

    existing = next(
        (
            location
            for location in existing_objects
            if _canonical_identity(location) == incoming_identity
        ),
        None,
    )
    if existing is not None:
        existing.aliases = list(dict.fromkeys([*(existing.aliases or []), *payload.aliases]))
        existing.required = sorted(set(existing.required or []) | set(payload.required))
        await existing.save(update_fields=["aliases", "required", "updated_at"])
        return existing

    return await LocationObject.create(
        aliases=payload.aliases,
        club=payload.club,
        city=payload.city,
        region=payload.region,
        required=sorted(payload.required),
    )


async def add_aliases_to_location_object(
    location_id: UUID,
    aliases: list[str],
) -> LocationObject:
    location = await LocationObject.get_or_none(id=location_id)
    if location is None:
        raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)

    new_aliases = [
        alias
        for alias in aliases
        if normalize_location_text(alias)
        not in {normalize_location_text(existing) for existing in (location.aliases or [])}
    ]
    if not new_aliases:
        return location

    for other in await LocationObject.exclude(id=location_id):
        duplicate_aliases = {
            normalize_location_text(alias)
            for alias in new_aliases
        } & {
            normalize_location_text(alias)
            for alias in (other.aliases or [])
        }
        if (
            duplicate_aliases
            and _canonical_identity(other) != _canonical_identity(location)
            and not (location.required and other.required)
        ):
            raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)

    location.aliases = list(dict.fromkeys([*(location.aliases or []), *new_aliases]))
    await location.save(update_fields=["aliases", "updated_at"])
    return location


async def search_location_entities(
    entity: LocationEntity,
    query: str,
    *,
    limit: int = 10,
    threshold: float = 0.2,
    region: Optional[str] = None,
    city: Optional[str] = None,
) -> list[LocationEntitySearchItem]:
    query_key = normalize_location_text(query)
    results: list[LocationEntitySearchItem] = []
    for location in await LocationObject.all():
        if not matches_required_location_context(location, region=region, city=city):
            continue
        if entity == "alias":
            names = location.aliases or []
        else:
            names = [getattr(location, entity)]
        for name in names:
            if not name:
                continue
            name_key = normalize_location_text(name)
            exact = name_key == query_key
            contains = query_key in name_key
            if not exact and not contains:
                continue
            results.append(
                LocationEntitySearchItem(
                    id=location.id,
                    name=name,
                    exact_match=exact,
                    similarity=1.0 if exact else max(threshold, 0.5),
                )
            )
    results.sort(key=lambda item: (not item.exact_match, -item.similarity, item.name))
    return results[:limit]
