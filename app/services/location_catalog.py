import re
import unicodedata
import uuid
from typing import Literal, Optional
from uuid import UUID

from tortoise import Tortoise
from tortoise.exceptions import IntegrityError

from app.core.errors import APIError, ErrorCode
from app.models.location.location_object import LocationObject
from app.schemas.location.location import (
    AthleteLocationCreate,
    LocationEntitySearchItem,
    LocationObjectCreate,
)

LocationEntity = Literal["alias", "club", "city", "region"]

_ENTITY_FIELDS: dict[LocationEntity, tuple[str, str]] = {
    "alias": ("alias", "id"),
    "club": ("club", "club_id"),
    "city": ("city", "city_id"),
    "region": ("region", "region_id"),
}
_UUID_NAMESPACE = uuid.uuid5(
    uuid.NAMESPACE_URL,
    "https://fincubes.ru/location-catalog",
)


def normalize_location_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    normalized = normalized.replace("ё", "е")
    return re.sub(r"\s+", " ", normalized)


def deterministic_entity_id(
    entity: Literal["club", "city", "region"],
    name: str,
) -> UUID:
    normalized = normalize_location_text(name)
    return uuid.uuid5(_UUID_NAMESPACE, f"{entity}:{normalized}")


def deterministic_location_object_id(
    club_id: Optional[UUID],
    city_id: Optional[UUID],
    region_id: UUID,
) -> UUID:
    identity = ":".join(
        str(value) if value is not None else "-"
        for value in (club_id, city_id, region_id)
    )
    return uuid.uuid5(_UUID_NAMESPACE, f"location-object:{identity}")


def legacy_club_value(
    observed_alias: str,
    canonical_club: Optional[str],
) -> Optional[str]:
    if len(observed_alias) <= 255:
        return observed_alias
    if canonical_club and len(canonical_club) <= 255:
        return canonical_club
    return None


def matches_required_location_context(
    location: LocationObject,
    *,
    region_id: Optional[UUID] = None,
    city_id: Optional[UUID] = None,
) -> bool:
    """Check only fields explicitly listed in ``location.required``."""

    if region_id is None and city_id is None:
        return True

    required = set(location.required or [])
    if "region" in required and location.region_id != region_id:
        return False
    if "city" in required and location.city_id != city_id:
        return False
    return True


async def find_exact_alias(
    alias: str,
    *,
    region_id: Optional[UUID] = None,
) -> Optional[LocationObject]:
    matches = [
        location
        for location in await LocationObject.all()
        if alias in (location.aliases or [])
        and (region_id is None or location.region_id == region_id)
    ]
    if len(matches) > 1:
        if region_id is None:
            raise APIError(ErrorCode.LOCATION_REGION_REQUIRED)
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)
    return matches[0] if matches else None


async def _find_exact_entity_id(
    entity: Literal["club", "city", "region"],
    name: str,
    *,
    region_id: Optional[UUID] = None,
) -> Optional[UUID]:
    field, id_field = _ENTITY_FIELDS[entity]
    filters = {field: name.strip()}
    if region_id is not None and entity == "city":
        filters["region_id"] = region_id

    rows = await LocationObject.filter(**filters).values(field, id_field)
    if not rows:
        fallback_filters = {}
        if region_id is not None and entity == "city":
            fallback_filters["region_id"] = region_id
        rows = await LocationObject.filter(**fallback_filters).values(
            field,
            id_field,
        )

    normalized = normalize_location_text(name)
    matches = {
        UUID(str(row[id_field]))
        for row in rows
        if row.get(field)
        and row.get(id_field)
        and normalize_location_text(str(row[field])) == normalized
    }
    if len(matches) > 1:
        raise APIError(ErrorCode.LOCATION_ENTITY_ID_CONFLICT)
    return next(iter(matches), None)


async def _resolve_entity_id(
    entity: Literal["club", "city", "region"],
    name: str,
    supplied_id: Optional[UUID],
    *,
    region_id: Optional[UUID] = None,
) -> UUID:
    exact_id = await _find_exact_entity_id(
        entity,
        name,
        region_id=region_id,
    )
    if exact_id is not None:
        if supplied_id is not None and supplied_id != exact_id:
            raise APIError(ErrorCode.LOCATION_ENTITY_ID_CONFLICT)
        return exact_id
    return supplied_id or deterministic_entity_id(entity, name)


async def create_location_object(
    payload: LocationObjectCreate,
) -> LocationObject:
    region_id = await _resolve_entity_id(
        "region",
        payload.region,
        payload.region_id,
    )
    city_id = None
    if payload.city:
        city_id = await _resolve_entity_id(
            "city",
            payload.city,
            payload.city_id,
            region_id=region_id,
        )
    club_id = None
    if payload.club:
        club_id = await _resolve_entity_id(
            "club",
            payload.club,
            payload.club_id,
        )

    object_id = deterministic_location_object_id(
        club_id,
        city_id,
        region_id,
    )
    existing_objects = await LocationObject.all()
    for location in existing_objects:
        duplicate_aliases = set(payload.aliases) & set(location.aliases or [])
        if duplicate_aliases and location.id != object_id:
            can_disambiguate_by_region = (
                location.region_id != region_id
                and "region" in set(location.required or [])
                and "region" in payload.required
            )
            if not can_disambiguate_by_region:
                raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT)

    existing = next(
        (location for location in existing_objects if location.id == object_id),
        None,
    )
    if existing is not None:
        existing.aliases = list(
            dict.fromkeys([*(existing.aliases or []), *payload.aliases])
        )
        if payload.required == {"region"}:
            existing.required = ["region"]
        else:
            existing.required = sorted(
                set(existing.required or []) | set(payload.required)
            )
        await existing.save(update_fields=["aliases", "required", "updated_at"])
        return existing

    try:
        return await LocationObject.create(
            id=object_id,
            aliases=payload.aliases,
            club=payload.club,
            club_id=club_id,
            city=payload.city,
            city_id=city_id,
            region=payload.region,
            region_id=region_id,
            required=sorted(payload.required),
        )
    except IntegrityError as exc:
        raise APIError(ErrorCode.LOCATION_ALIAS_CONFLICT) from exc


async def resolve_location_link(
    payload: AthleteLocationCreate,
) -> LocationObject:
    location = await LocationObject.get_or_none(id=payload.location_id)
    if location is None:
        raise APIError(ErrorCode.LOCATION_ALIAS_NOT_FOUND)
    if payload.alias not in (location.aliases or []):
        raise APIError(ErrorCode.LOCATION_ALIAS_MISMATCH)
    return location


async def search_location_entities(
    entity: LocationEntity,
    query: str,
    *,
    limit: int = 10,
    threshold: float = 0.2,
    region_id: Optional[UUID] = None,
    city_id: Optional[UUID] = None,
) -> list[LocationEntitySearchItem]:
    params: list[object] = [query.strip(), threshold]
    context_conditions: list[str] = []
    if region_id is not None and entity in {"alias", "club", "city"}:
        params.append(region_id)
        context_conditions.append(
            f'"location_objects"."region_id" = ${len(params)}'
        )
    if city_id is not None and entity in {"alias", "club"}:
        params.append(city_id)
        context_conditions.append(
            f'"location_objects"."city_id" = ${len(params)}'
        )

    if entity == "alias":
        name_sql = '"alias_value"'
        id_sql = '"location_objects"."id"'
        from_sql = (
            '"location_objects" CROSS JOIN LATERAL '
            'jsonb_array_elements_text("aliases") '
            'AS alias_rows("alias_value")'
        )
        base_conditions = []
    else:
        field, id_field = _ENTITY_FIELDS[entity]
        name_sql = f'"location_objects"."{field}"'
        id_sql = f'"location_objects"."{id_field}"'
        from_sql = '"location_objects"'
        base_conditions = [
            f'"location_objects"."{field}" IS NOT NULL',
            f'"location_objects"."{id_field}" IS NOT NULL',
        ]

    conditions = [
        *base_conditions,
        (
            f"(LOWER({name_sql}) = LOWER($1) "
            f"OR {name_sql} ILIKE '%' || $1 || '%' "
            f"OR similarity({name_sql}, $1) >= $2)"
        ),
        *context_conditions,
    ]
    params.append(limit)
    where_sql = " AND ".join(conditions)
    sql = f"""
        SELECT
            {id_sql} AS "id",
            {name_sql} AS "name",
            MAX(similarity({name_sql}, $1)) AS "similarity"
        FROM {from_sql}
        WHERE {where_sql}
        GROUP BY {id_sql}, {name_sql}
        ORDER BY
            CASE WHEN LOWER({name_sql}) = LOWER($1) THEN 0 ELSE 1 END,
            "similarity" DESC,
            "name" ASC
        LIMIT ${len(params)}
    """
    rows = await Tortoise.get_connection("default").execute_query_dict(
        sql,
        params,
    )
    normalized_query = normalize_location_text(query)
    return [
        LocationEntitySearchItem(
            id=UUID(str(row["id"])),
            name=row["name"],
            exact_match=(
                normalize_location_text(row["name"]) == normalized_query
            ),
            similarity=max(0.0, min(1.0, float(row["similarity"] or 0))),
        )
        for row in rows
    ]
