from typing import Literal, Optional
from uuid import UUID

from tortoise.transactions import in_transaction

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.location.location_alias import LocationAlias
from app.models.location.location_object import LocationObject
from app.schemas.location.location import (
    LocationAliasOut,
    LocationAliasUpdate,
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
from app.shared.utils.location_text import normalize_location_text

LocationEntity = Literal["alias", "club", "city", "region"]


def _matches_text(value: str | None, expected: str | None) -> bool:
    if expected is None:
        return False
    return bool(value) and normalize_location_text(value) == normalize_location_text(expected)


def matches_required_location_context(
    location: LocationObject,
    *,
    region: Optional[str] = None,
    city: Optional[str] = None,
    required: Optional[list[str] | set[str]] = None,
) -> bool:
    required_fields = set(required or [])
    if "region" in required_fields and not _matches_text(location.region, region):
        return False
    if "city" in required_fields and not _matches_text(location.city, city):
        return False
    return True


async def _alias_matches(alias: str) -> list[LocationAlias]:
    return await LocationAlias.filter(
        alias_key=normalize_location_text(alias),
    ).prefetch_related("location_object")


def _canonical_identity(location: LocationObject) -> tuple[str, str, str]:
    return (
        normalize_location_text(location.club or ""),
        normalize_location_text(location.city or ""),
        normalize_location_text(location.region),
    )


async def location_object_out(location: LocationObject) -> LocationObjectOut:
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


async def _assert_aliases_can_be_used(
    *,
    location: LocationObject,
    aliases: list[str],
    required: set[str] | list[str],
    exclude_alias_id: Optional[UUID] = None,
) -> None:
    location_identity = _canonical_identity(location)
    required_fields = set(required or [])
    incoming_alias_keys = {normalize_location_text(alias) for alias in aliases}

    existing_aliases = await LocationAlias.filter(
        alias_key__in=incoming_alias_keys,
    ).prefetch_related("location_object")

    for existing in existing_aliases:
        if exclude_alias_id is not None and existing.id == exclude_alias_id:
            continue
        if existing.location_object_id == location.id:
            raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)
        if _canonical_identity(existing.location_object) == location_identity:
            continue
        if not (required_fields and set(existing.required or [])):
            raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)


async def _create_alias_rules(
    location: LocationObject,
    aliases: list[str],
    required: set[str] | list[str],
) -> None:
    await _assert_aliases_can_be_used(
        location=location,
        aliases=aliases,
        required=required,
    )
    for alias in aliases:
        await LocationAlias.create(
            location_object=location,
            alias=alias,
            alias_key=normalize_location_text(alias),
            required=sorted(required or []),
        )


async def find_exact_alias(
    alias: str,
    *,
    region: Optional[str] = None,
    city: Optional[str] = None,
) -> Optional[LocationObject]:
    matches = await _alias_matches(alias)
    if not matches:
        return None

    contextual_matches = [
        match
        for match in matches
        if matches_required_location_context(
            match.location_object,
            region=region,
            city=city,
            required=match.required,
        )
    ]
    if len(contextual_matches) == 1:
        return contextual_matches[0].location_object
    if len(contextual_matches) > 1:
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)

    if any("city" in set(match.required or []) for match in matches):
        raise APIError(ErrorCode.LOCATION_REGION_REQUIRED)
    if any("region" in set(match.required or []) for match in matches):
        raise APIError(ErrorCode.LOCATION_REGION_REQUIRED)
    if len(matches) > 1:
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)
    return matches[0].location_object


async def resolve_location_alias(
    payload: LocationResolveRequest,
) -> Optional[LocationResolveResult]:
    matches = await _alias_matches(payload.alias)
    if not matches:
        return None

    contextual_matches = [
        match
        for match in matches
        if matches_required_location_context(
            match.location_object,
            city=payload.city,
            region=payload.region,
            required=match.required,
        )
    ]
    if len(contextual_matches) != 1:
        await find_exact_alias(payload.alias, city=payload.city, region=payload.region)
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)

    alias_rule = contextual_matches[0]
    location = alias_rule.location_object
    return LocationResolveResult(
        id=location.id,
        alias_id=alias_rule.id,
        alias=alias_rule.alias,
        club=location.club,
        city=location.city,
        region=location.region,
        required=sorted(alias_rule.required or []),
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


async def resolve_athlete_location_object(
    *,
    alias: Optional[str] = None,
    club: Optional[str],
    city: Optional[str],
    region: Optional[str],
    create_missing_alias: bool = True,
) -> Optional[LocationObject]:
    if not alias:
        return await get_or_create_location_object_by_identity(
            club=club,
            city=city,
            region=region,
        )

    resolved = await find_exact_alias(
        alias,
        city=city,
        region=region,
    )
    if resolved is not None:
        return resolved

    if not create_missing_alias or not region:
        return None

    return await create_location_object(
        LocationObjectCreate(
            aliases=[alias],
            club=club,
            city=city,
            region=region,
        )
    )


async def get_or_create_location_object_by_identity(
    *,
    club: Optional[str],
    city: Optional[str],
    region: Optional[str],
) -> Optional[LocationObject]:
    if not region:
        return None

    incoming_identity = (
        normalize_location_text(club or ""),
        normalize_location_text(city or ""),
        normalize_location_text(region),
    )
    existing = next(
        (
            location
            for location in await LocationObject.all()
            if _canonical_identity(location) == incoming_identity
        ),
        None,
    )
    if existing is not None:
        return existing

    return await LocationObject.create(
        club=club,
        city=city,
        region=region,
    )


async def get_location_object_or_error(location_object_id: UUID) -> LocationObject:
    location = await LocationObject.get_or_none(id=location_object_id)
    if location is None:
        raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)
    return location


async def resolve_athlete_location_update(
    *,
    location_object_id: Optional[UUID] = None,
    alias: Optional[str] = None,
    club: Optional[str] = None,
    city: Optional[str] = None,
    region: Optional[str] = None,
) -> Optional[LocationObject]:
    if location_object_id is not None:
        return await get_location_object_or_error(location_object_id)

    if any(value is not None for value in (alias, club, city, region)):
        return await resolve_athlete_location_object(
            alias=alias,
            club=club,
            city=city,
            region=region,
        )

    return None


async def create_location_object(
    payload: LocationObjectCreate,
) -> LocationObject:
    existing_objects = await LocationObject.all()
    incoming_identity = (
        normalize_location_text(payload.club or ""),
        normalize_location_text(payload.city or ""),
        normalize_location_text(payload.region),
    )

    existing = next(
        (
            location
            for location in existing_objects
            if _canonical_identity(location) == incoming_identity
        ),
        None,
    )
    if existing is not None:
        await add_aliases_to_location_object(
            existing.id,
            payload.aliases,
            payload.required,
        )
        return existing

    created = await LocationObject.create(
        club=payload.club,
        city=payload.city,
        region=payload.region,
    )
    await _create_alias_rules(created, payload.aliases, payload.required)
    return created


async def add_aliases_to_location_object(
    location_id: UUID,
    aliases: list[str],
    required: set[str] | list[str] | None = None,
) -> LocationObject:
    location = await LocationObject.get_or_none(id=location_id)
    if location is None:
        raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)

    existing_keys = {
        alias.alias_key
        for alias in await LocationAlias.filter(location_object=location)
    }
    new_aliases = [
        alias
        for alias in aliases
        if normalize_location_text(alias) not in existing_keys
    ]
    if not new_aliases:
        return location

    await _create_alias_rules(location, new_aliases, required or [])
    return location


async def update_location_alias(
    alias_id: UUID,
    payload: LocationAliasUpdate,
) -> LocationAlias:
    alias_rule = await LocationAlias.get_or_none(id=alias_id).prefetch_related(
        "location_object",
    )
    if alias_rule is None:
        raise APIError(ErrorCode.LOCATION_ALIAS_NOT_FOUND)

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return alias_rule

    new_alias = data.get("alias", alias_rule.alias)
    new_required = data.get("required", set(alias_rule.required or []))
    await _assert_aliases_can_be_used(
        location=alias_rule.location_object,
        aliases=[new_alias],
        required=new_required,
        exclude_alias_id=alias_rule.id,
    )

    alias_rule.alias = new_alias
    alias_rule.alias_key = normalize_location_text(new_alias)
    alias_rule.required = sorted(new_required)
    await alias_rule.save(update_fields=["alias", "alias_key", "required", "updated_at"])
    return alias_rule


async def delete_location_alias(alias_id: UUID) -> None:
    deleted = await LocationAlias.filter(id=alias_id).delete()
    if not deleted:
        raise APIError(ErrorCode.LOCATION_ALIAS_NOT_FOUND)


async def preview_location_merge(
    source_location_id: UUID,
    target_location_id: UUID,
) -> LocationMergePreview:
    if source_location_id == target_location_id:
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)

    source = await LocationObject.get_or_none(id=source_location_id)
    target = await LocationObject.get_or_none(id=target_location_id)
    if source is None or target is None:
        raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)

    athletes_to_move = await Athlete.filter(
        location_object_id=source_location_id,
    ).count()
    source_aliases = await LocationAlias.filter(
        location_object_id=source_location_id,
    ).order_by("alias")
    target_alias_keys = {
        alias.alias_key
        for alias in await LocationAlias.filter(location_object_id=target_location_id)
    }

    aliases_to_move = [
        alias.alias
        for alias in source_aliases
        if alias.alias_key not in target_alias_keys
    ]
    duplicate_aliases = [
        alias.alias
        for alias in source_aliases
        if alias.alias_key in target_alias_keys
    ]

    return LocationMergePreview(
        source=await location_object_out(source),
        target=await location_object_out(target),
        athletes_to_move=athletes_to_move,
        aliases_to_move=aliases_to_move,
        duplicate_aliases=duplicate_aliases,
    )


async def merge_location_object(
    source_location_id: UUID,
    payload: LocationMergeRequest,
) -> LocationMergeResult:
    if source_location_id == payload.target_location_id:
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)

    source = await LocationObject.get_or_none(id=source_location_id)
    target = await LocationObject.get_or_none(id=payload.target_location_id)
    if source is None or target is None:
        raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)

    preview = await preview_location_merge(source_location_id, payload.target_location_id)

    async with in_transaction():
        moved_athletes = await Athlete.filter(
            location_object_id=source_location_id,
        ).update(location_object_id=payload.target_location_id)

        moved_aliases = 0
        duplicate_aliases: list[str] = []
        if payload.move_aliases:
            target_alias_keys = {
                alias.alias_key
                for alias in await LocationAlias.filter(
                    location_object_id=payload.target_location_id,
                )
            }
            source_aliases = await LocationAlias.filter(
                location_object_id=source_location_id,
            ).order_by("alias")
            for alias in source_aliases:
                if alias.alias_key in target_alias_keys:
                    duplicate_aliases.append(alias.alias)
                    await alias.delete()
                    continue
                alias.location_object_id = payload.target_location_id
                await alias.save(update_fields=["location_object_id", "updated_at"])
                target_alias_keys.add(alias.alias_key)
                moved_aliases += 1
        else:
            duplicate_aliases = preview.duplicate_aliases

        deleted_source_id = None
        if payload.delete_source:
            await source.delete()
            deleted_source_id = source_location_id

    target = await LocationObject.get(id=payload.target_location_id)
    return LocationMergeResult(
        target=await location_object_out(target),
        deleted_source_id=deleted_source_id,
        moved_athletes=moved_athletes,
        moved_aliases=moved_aliases,
        duplicate_aliases=duplicate_aliases,
    )


async def update_location_object(
    location_id: UUID,
    payload: LocationObjectUpdate,
) -> LocationObject:
    location = await LocationObject.get_or_none(id=location_id)
    if location is None:
        raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)

    data = payload.model_dump(exclude_unset=True)
    if not data:
        return location

    location.club = data.get("club", location.club)
    location.city = data.get("city", location.city)
    location.region = data.get("region", location.region)
    await location.save(update_fields=["club", "city", "region", "updated_at"])
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

    if entity == "alias":
        aliases = await LocationAlias.all().prefetch_related("location_object")
        for alias_rule in aliases:
            location = alias_rule.location_object
            if not matches_required_location_context(
                location,
                region=region,
                city=city,
                required=alias_rule.required,
            ):
                continue
            name_key = normalize_location_text(alias_rule.alias)
            exact = name_key == query_key
            contains = query_key in name_key
            if not exact and not contains:
                continue
            results.append(
                LocationEntitySearchItem(
                    id=location.id,
                    name=alias_rule.alias,
                    exact_match=exact,
                    similarity=1.0 if exact else max(threshold, 0.5),
                )
            )
    else:
        for location in await LocationObject.all():
            name = getattr(location, entity)
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
