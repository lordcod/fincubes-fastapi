"""Import reviewed alias groups into simplified ``location_objects``."""

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tortoise import Tortoise

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.data.location_additions import locations as location_additions
from app.data.location_aliases import locations as legacy_locations
from app.models.location.location_object import LocationObject
from app.services.location_catalog import (
    add_aliases_to_location_object,
    create_location_object,
    normalize_location_text,
)
from app.schemas.location.location import LocationObjectCreate

_UNRESOLVED_REGION = "не определён"


@dataclass
class ImportSummary:
    aliases: int = 0
    objects: int = 0
    created: int = 0
    updated: int = 0
    invalid: int = 0


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


def _identity(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        normalize_location_text(row.get("club") or ""),
        normalize_location_text(row.get("city") or ""),
        normalize_location_text(row["region"]),
    )


def build_location_objects() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    invalid: list[dict[str, str]] = []

    for row in _source_rows():
        aliases = row["aliases"]
        region = row.get("region")
        if not region or normalize_location_text(region) == normalize_location_text(
            _UNRESOLVED_REGION
        ):
            invalid.extend(
                {"alias": alias, "reason": "region is required"}
                for alias in aliases
            )
            continue

        key = _identity(row)
        existing = grouped.get(key)
        if existing is None:
            grouped[key] = {
                "aliases": list(dict.fromkeys(aliases)),
                "club": row.get("club"),
                "city": row.get("city"),
                "region": region,
                "required": sorted(row.get("required") or []),
            }
            continue

        existing["aliases"] = list(
            dict.fromkeys([*existing["aliases"], *aliases])
        )
        existing["required"] = sorted(
            set(existing["required"]) | set(row.get("required") or [])
        )

    return list(grouped.values()), invalid


async def _find_existing(row: dict[str, Any]) -> LocationObject | None:
    key = _identity(row)
    for location in await LocationObject.all():
        candidate = {
            "club": location.club,
            "city": location.city,
            "region": location.region,
        }
        if _identity(candidate) == key:
            return location
    return None


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
        location = await _find_existing(row)
        if location is None:
            await create_location_object(LocationObjectCreate(**row))
            summary.created += 1
            continue

        location.club = row["club"]
        location.city = row["city"]
        location.region = row["region"]
        await location.save(
            update_fields=["club", "city", "region", "updated_at"]
        )
        await add_aliases_to_location_object(
            location.id,
            row["aliases"],
            row["required"],
        )
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
