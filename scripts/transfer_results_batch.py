from app.services.admin_maintenance import transfer_results
from app.models import Athlete, RelayLeg, Result
import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from tortoise import Tortoise

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_PAIRS = """"""


@dataclass(frozen=True)
class TransferPair:
    source_id: int
    target_id: int


def parse_pairs(raw: str) -> list[TransferPair]:
    pairs = []
    for line_number, line in enumerate(raw.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split(";")]
        if len(parts) != 2:
            raise ValueError(f"Invalid pair at line {line_number}: {line!r}")
        pairs.append(TransferPair(int(parts[0]), int(parts[1])))
    return pairs


def read_pairs(path: str | None) -> list[TransferPair]:
    if path is None:
        return parse_pairs(DEFAULT_PAIRS)
    with open(path, encoding="utf-8") as file:
        return parse_pairs(file.read())


def athlete_name(snapshot) -> str:
    if snapshot is None:
        return "-"
    return f"{snapshot.last_name} {snapshot.first_name}".strip()


async def run_batch(args) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    db_url = args.database_url or os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL is required. Pass --database-url or set DATABASE_URL.")
        return 2

    pairs = read_pairs(args.pairs_file)
    await Tortoise.init(db_url=db_url, modules={"models": ["app.models"]})
    try:
        dry_results = []
        problems = []

        print(f"Preflight dry-run: {len(pairs)} pair(s)")
        for pair in pairs:
            result = await transfer_results(
                from_athlete_id=pair.source_id,
                to_athlete_id=pair.target_id,
                competition_id=args.competition_id,
                apply=False,
                delete_empty_source=args.delete_empty_source,
            )
            dry_results.append(result)

            has_problem = any(
                "not found" in message
                or "must be different" in message
                for message in result.messages
            )
            if has_problem:
                problems.append((pair, result))

            print(
                f"DRY {pair.source_id}->{pair.target_id}: "
                f"affected={result.affected}, "
                f"individual={result.individual_results}, "
                f"relay_legs={result.relay_legs}, "
                f"from={athlete_name(result.from_athlete)}, "
                f"to={athlete_name(result.to_athlete)}"
            )
            for message in result.messages:
                print(f"  {message}")

        total_affected = sum(result.affected for result in dry_results)
        zero_count = sum(1 for result in dry_results if result.affected == 0)
        print(
            f"Dry-run summary: pairs={len(pairs)}, "
            f"affected={total_affected}, zero={zero_count}, "
            f"problems={len(problems)}"
        )

        if problems:
            print("Aborted: fix missing/invalid pairs first.")
            return 2

        if not args.apply:
            print("No changes applied. Re-run with --apply to update the database.")
            return 0

        print("Applying changes...")
        applied_total = 0
        deleted_sources = 0
        for pair in pairs:
            result = await transfer_results(
                from_athlete_id=pair.source_id,
                to_athlete_id=pair.target_id,
                competition_id=args.competition_id,
                apply=True,
                delete_empty_source=args.delete_empty_source,
            )
            applied_total += result.affected
            deleted_sources += int(result.deleted_source_athlete)
            print(
                f"APPLY {pair.source_id}->{pair.target_id}: "
                f"affected={result.affected}, "
                f"individual={result.individual_results}, "
                f"relay_legs={result.relay_legs}, "
                f"deleted_source={result.deleted_source_athlete}, "
                f"remaining_individual={result.remaining_source_results}, "
                f"remaining_relay_legs={result.remaining_source_relay_legs}"
            )
            for message in result.messages:
                print(f"  {message}")

        print(
            f"Apply summary: pairs={len(pairs)}, "
            f"affected={applied_total}, deleted_sources={deleted_sources}"
        )
        remaining_sources = []
        missing_targets = []
        for pair in pairs:
            source_individual = await Result.filter(athlete_id=pair.source_id).count()
            source_relay_legs = await RelayLeg.filter(athlete_id=pair.source_id).count()
            source_exists = await Athlete.filter(id=pair.source_id).exists()
            target_exists = await Athlete.filter(id=pair.target_id).exists()
            if source_individual or source_relay_legs or source_exists:
                remaining_sources.append(
                    (
                        pair,
                        source_exists,
                        source_individual,
                        source_relay_legs,
                    )
                )
            if not target_exists:
                missing_targets.append(pair)

        print(
            f"Verification summary: remaining_sources={len(remaining_sources)}, "
            f"missing_targets={len(missing_targets)}"
        )
        for pair, source_exists, source_individual, source_relay_legs in remaining_sources:
            print(
                f"  SOURCE {pair.source_id}: exists={source_exists}, "
                f"individual={source_individual}, relay_legs={source_relay_legs}"
            )
        for pair in missing_targets:
            print(
                f"  TARGET MISSING {pair.target_id} for pair {pair.source_id}->{pair.target_id}")
        if remaining_sources or missing_targets:
            return 3
        return 0
    finally:
        await Tortoise.close_connections()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Batch transfer individual results and relay legs between athlete IDs.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually update database rows. Without this flag the script only dry-runs.",
    )
    parser.add_argument(
        "--database-url",
        help="Tortoise database URL. Defaults to DATABASE_URL from environment.",
    )
    parser.add_argument(
        "--competition-id",
        type=int,
        help="Limit transfers to one competition.",
    )
    parser.add_argument(
        "--pairs-file",
        help="Optional UTF-8 file with lines in 'from_id;to_id' format.",
    )
    parser.add_argument(
        "--keep-source",
        dest="delete_empty_source",
        action="store_false",
        help="Do not delete source athletes after they become empty.",
    )
    parser.set_defaults(delete_empty_source=True)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_batch(args)))


if __name__ == "__main__":
    main()
