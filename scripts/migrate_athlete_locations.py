"""Link legacy ``athletes.club`` values to the normalized alias catalog.

The script is idempotent. Non-empty legacy aliases that cannot be matched are
written to JSON and are never converted implicitly. If one alias belongs to
several reviewed objects, ``athletes.city`` is used as the discriminator.

Usage:
    python scripts/migrate_athlete_locations.py --dry-run
    python scripts/migrate_athlete_locations.py --output unmatched.json
"""

import argparse
import asyncio
import json
from pathlib import Path
from typing import Optional

from tortoise import Tortoise

from app.models.athlete.athlete import Athlete
from app.models.location.athlete_location import AthleteLocation
from app.models.location.location_object import LocationObject
from app.services.location_catalog import normalize_location_text


def _append_unique(
    index: dict[str, list[LocationObject]],
    key: str,
    location: LocationObject,
) -> None:
    values = index.setdefault(key, [])
    if all(existing.id != location.id for existing in values):
        values.append(location)


def _select_by_city(
    candidates: list[LocationObject],
    city: Optional[str],
) -> Optional[LocationObject]:
    if len(candidates) == 1:
        return candidates[0]
    if not city or not city.strip():
        return None

    city_key = normalize_location_text(city)
    city_matches = [
        location
        for location in candidates
        if location.city
        and normalize_location_text(location.city) == city_key
    ]
    return city_matches[0] if len(city_matches) == 1 else None


def _candidate_export(
    candidates: list[LocationObject],
) -> list[dict[str, object]]:
    return [
        {
            "location_id": str(location.id),
            "city": location.city,
            "region": location.region,
            "region_id": str(location.region_id),
        }
        for location in candidates
    ]


async def migrate(*, dry_run: bool) -> tuple[dict[str, int], list[dict]]:
    objects = await LocationObject.all()
    aliases_by_literal: dict[str, list[LocationObject]] = {}
    aliases_by_key: dict[str, list[LocationObject]] = {}
    for location in objects:
        for alias in location.aliases or []:
            _append_unique(aliases_by_literal, alias, location)
            _append_unique(
                aliases_by_key,
                normalize_location_text(alias),
                location,
            )

    summary = {
        "athletes": 0,
        "linked": 0,
        "already_linked": 0,
        "without_alias": 0,
        "unmatched": 0,
        "ambiguous": 0,
    }
    missing: list[dict] = []

    async for athlete in Athlete.all().order_by("id"):
        summary["athletes"] += 1
        if not athlete.club or not athlete.club.strip():
            summary["without_alias"] += 1
            continue

        candidates = aliases_by_literal.get(athlete.club)
        if candidates is None:
            candidates = aliases_by_key.get(
                normalize_location_text(athlete.club)
            )

        if not candidates:
            summary["unmatched"] += 1
            missing.append(
                {
                    "athlete_id": athlete.id,
                    "club": athlete.club,
                    "city": athlete.city,
                    "reason": "alias not found",
                }
            )
            continue

        location_object = _select_by_city(candidates, athlete.city)
        if location_object is None:
            summary["ambiguous"] += 1
            missing.append(
                {
                    "athlete_id": athlete.id,
                    "club": athlete.club,
                    "city": athlete.city,
                    "reason": "alias requires location context",
                    "candidates": _candidate_export(candidates),
                }
            )
            continue

        exists = await AthleteLocation.filter(
            athlete_id=athlete.id,
            location_object_id=location_object.id,
            alias=athlete.club,
        ).exists()
        if exists:
            summary["already_linked"] += 1
            continue

        if not dry_run:
            await AthleteLocation.create(
                athlete=athlete,
                location_object=location_object,
                alias=athlete.club,
            )
        summary["linked"] += 1

    return summary, missing


async def run(args: argparse.Namespace) -> None:
    from app.core.config.tortoise_orm import TORTOISE_ORM

    await Tortoise.init(config=TORTOISE_ORM)
    try:
        summary, missing = await migrate(dry_run=args.dry_run)
    finally:
        await Tortoise.close_connections()

    output = Path(args.output).resolve()
    output.write_text(
        json.dumps(missing, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    print(f"unmatched export: {output}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--output",
        default="athlete-location-unmatched.json",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
