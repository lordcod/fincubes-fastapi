"""Import reviewed alias groups into normalized ``location_objects``."""

import argparse
import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from tortoise import Tortoise

from app.data.location_additions import locations as location_additions
from app.data.location_aliases import locations as legacy_locations
from app.models.location.location_object import LocationObject
from app.services.location_catalog import (
    deterministic_entity_id,
    deterministic_location_object_id,
    normalize_location_text,
)

_UNRESOLVED_REGION = "не определён"


@dataclass
class ImportSummary:
    aliases: int = 0
    objects: int = 0
    created: int = 0
    updated: int = 0
    invalid: int = 0


def _entity_ids(entity: str, name_key: str, id_key: str) -> dict[str, UUID]:
    """Collect authoritative IDs from the original catalog only."""

    result: dict[str, UUID] = {}
    for value in legacy_locations.values():
        name = value.get(name_key)
        entity_id = value.get(id_key)
        if not name or not entity_id:
            continue
        normalized = normalize_location_text(name)
        parsed_id = UUID(str(entity_id))
        previous = result.get(normalized)
        if previous is not None and previous != parsed_id:
            raise ValueError(
                f"{entity} {name!r} связан с несколькими ID: "
                f"{previous} и {parsed_id}"
            )
        result[normalized] = parsed_id
    return result


def _source_rows() -> list[dict[str, Any]]:
    rows = [
        {
            "aliases": [alias],
            "club": value.get("club"),
            "city": value.get("city"),
            "region": value.get("region"),
            "required": sorted(value.get("required") or []),
        }
        for alias, value in legacy_locations.items()
    ]
    for item in location_additions:
        rows.append(
            {
                "aliases": list(item.get("aliases") or [item["name"]]),
                "club": item["name"],
                "city": item.get("city"),
                "region": item.get("region"),
                "required": sorted(item.get("required") or []),
            }
        )
    return rows


def build_location_objects(
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    known_ids = {
        "club": _entity_ids("club", "club", "club_id"),
        "city": _entity_ids("city", "city", "city_id"),
        "region": _entity_ids("region", "region", "region_id"),
    }
    grouped: dict[UUID, dict[str, Any]] = {}
    invalid: list[dict[str, str]] = []

    for value in _source_rows():
        aliases = value["aliases"]
        region = value.get("region")
        if not region or normalize_location_text(region) == normalize_location_text(
            _UNRESOLVED_REGION
        ):
            invalid.extend(
                {"alias": alias, "reason": "region is required"}
                for alias in aliases
            )
            continue

        resolved: dict[str, Any] = {
            "club": value.get("club"),
            "city": value.get("city"),
            "region": region,
        }
        for entity in ("club", "city", "region"):
            name = resolved.get(entity)
            if not name:
                resolved[f"{entity}_id"] = None
                continue
            normalized = normalize_location_text(name)
            entity_id = known_ids[entity].get(normalized)
            if entity_id is None:
                entity_id = deterministic_entity_id(entity, name)
                known_ids[entity][normalized] = entity_id
            resolved[f"{entity}_id"] = entity_id

        object_id = deterministic_location_object_id(
            resolved["club_id"],
            resolved["city_id"],
            resolved["region_id"],
        )
        existing = grouped.get(object_id)
        if existing is None:
            grouped[object_id] = {
                "id": object_id,
                "aliases": list(dict.fromkeys(aliases)),
                **resolved,
                "required": sorted(value.get("required") or []),
            }
            continue

        for field in (
            "club",
            "club_id",
            "city",
            "city_id",
            "region",
            "region_id",
        ):
            if existing[field] != resolved[field]:
                if (
                    field in {"club", "city", "region"}
                    and existing[field]
                    and resolved[field]
                    and normalize_location_text(existing[field])
                    == normalize_location_text(resolved[field])
                ):
                    continue
                raise ValueError(
                    f"Объект {object_id} содержит разные {field}: "
                    f"{existing[field]!r} и {resolved[field]!r}"
                )
        existing["aliases"] = list(
            dict.fromkeys([*existing["aliases"], *aliases])
        )
        incoming_required = set(value.get("required") or [])
        if incoming_required == {"region"}:
            existing["required"] = ["region"]
        else:
            existing["required"] = sorted(
                set(existing["required"]) | incoming_required
            )

    return list(grouped.values()), invalid


async def import_catalog(*, dry_run: bool) -> ImportSummary:
    objects, invalid = build_location_objects()
    summary = ImportSummary(
        aliases=sum(len(item["aliases"]) for item in objects),
        objects=len(objects),
        invalid=len(invalid),
    )
    if dry_run:
        summary.created = len(objects)
        return summary

    for row in objects:
        object_id = row["id"]
        defaults = {key: value for key, value in row.items() if key != "id"}
        location = await LocationObject.get_or_none(id=object_id)
        if location is None:
            await LocationObject.create(**row)
            summary.created += 1
        else:
            location.update_from_dict(defaults)
            await location.save()
            summary.updated += 1
    return summary


async def run(args: argparse.Namespace) -> None:
    objects, invalid = build_location_objects()
    if invalid:
        for item in invalid:
            print(f"SKIP {item['alias']!r}: {item['reason']}")

    if args.dry_run:
        print(
            f"dry-run: aliases={sum(len(item['aliases']) for item in objects)} "
            f"objects={len(objects)} invalid={len(invalid)}"
        )
        return

    from app.core.config.tortoise_orm import TORTOISE_ORM

    await Tortoise.init(config=TORTOISE_ORM)
    try:
        summary = await import_catalog(dry_run=False)
    finally:
        await Tortoise.close_connections()

    print(
        f"aliases={summary.aliases} objects={summary.objects} "
        f"created={summary.created} updated={summary.updated} "
        f"invalid={summary.invalid}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
