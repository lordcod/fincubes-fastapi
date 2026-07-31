"""Normalize existing athlete club/city/region fields from location aliases.

Usage:
    python scripts/migrate_athlete_locations.py --dry-run
    python scripts/migrate_athlete_locations.py --apply --output unmatched.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from tortoise import Tortoise

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.errors import APIError
from app.models import Athlete
from app.services.location_catalog import resolve_athlete_location_fields


async def migrate(*, apply: bool, overwrite: bool) -> tuple[dict[str, int], list[dict[str, Any]]]:
    summary = {
        "athletes": 0,
        "without_club": 0,
        "changed": 0,
        "unchanged": 0,
        "unmatched": 0,
        "conflict": 0,
    }
    unresolved: list[dict[str, Any]] = []

    async for athlete in Athlete.all().order_by("id"):
        summary["athletes"] += 1
        if not athlete.club or not athlete.club.strip():
            summary["without_club"] += 1
            continue

        before = {
            "club": athlete.club,
            "city": athlete.city,
            "region": athlete.region,
        }
        try:
            resolved = await resolve_athlete_location_fields(
                alias=athlete.club,
                club=athlete.club,
                city=athlete.city,
                region=athlete.region,
                create_missing_alias=apply,
            )
        except APIError as exc:
            summary["conflict"] += 1
            unresolved.append(
                {
                    "athlete_id": athlete.id,
                    "before": before,
                    "reason": exc.error_name,
                }
            )
            continue

        if resolved == before:
            summary["unmatched"] += 1
            unresolved.append(
                {
                    "athlete_id": athlete.id,
                    "before": before,
                    "reason": "alias not found",
                }
            )
            continue

        changes = {}
        for field, value in resolved.items():
            current = before[field]
            if current and current != value and not overwrite:
                continue
            if current != value:
                changes[field] = value

        if not changes:
            summary["unchanged"] += 1
            continue

        if apply:
            for field, value in changes.items():
                setattr(athlete, field, value)
            await athlete.save(update_fields=[*changes, "updated_at"])
        summary["changed"] += 1

    return summary, unresolved


async def run(args: argparse.Namespace) -> int:
    from app.core.config.tortoise_orm import TORTOISE_ORM

    await Tortoise.init(config=TORTOISE_ORM)
    try:
        summary, unresolved = await migrate(apply=args.apply, overwrite=args.overwrite)
    finally:
        await Tortoise.close_connections()

    output = Path(args.output).resolve()
    output.write_text(
        json.dumps(unresolved, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({**summary, "apply": args.apply}, ensure_ascii=False))
    print(f"unresolved export: {output}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="Kept for old command compatibility.")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--output", default="athlete-location-unresolved.json")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
