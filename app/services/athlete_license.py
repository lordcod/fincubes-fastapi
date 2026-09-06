"""Derive athlete sports ranks from their individual results."""

import logging
from collections import defaultdict
from typing import Iterable

from app.models.athlete.athlete import Athlete
from app.models.competition.result import Result


logger = logging.getLogger(__name__)


# The order is intentionally limited to the ranks managed automatically.
# Values above КМС are maintained by an administrator and are never replaced.
AUTOMATIC_LICENSE_ORDER = (
    "IIIЮН",
    "IIЮН",
    "IЮН",
    "III",
    "II",
    "I",
    "КМС",
)

MANUAL_LICENSES = frozenset({"МС", "МСМК", "ЗМС"})


def normalize_license(value: str | None) -> str | None:
    if value is None:
        return None
    value = " ".join(value.strip().upper().split())
    compact = value.replace(" ", "")
    aliases = {
        "1": "I",
        "2": "II",
        "3": "III",
        "I ЮН": "IЮН",
        "II ЮН": "IIЮН",
        "III ЮН": "IIIЮН",
        "IЮН": "IЮН",
        "IIЮН": "IIЮН",
        "IIIЮН": "IIIЮН",
        "I ЮНОШЕСКИЙ": "IЮН",
        "II ЮНОШЕСКИЙ": "IIЮН",
        "III ЮНОШЕСКИЙ": "IIIЮН",
        "КМС": "КМС",
        "CMS": "КМС",
        "МСМК": "МСМК",
        "MSMK": "МСМК",
        "МС": "МС",
        "MS": "МС",
    }
    return aliases.get(value, aliases.get(compact, compact))


def highest_automatic_license(values: Iterable[str | None]) -> str | None:
    ranks = {
        rank.upper(): rank
        for rank in AUTOMATIC_LICENSE_ORDER
    }
    available = [
        (index, ranks[normalized])
        for value in values
        if (normalized := normalize_license(value)) in ranks
        for index in [AUTOMATIC_LICENSE_ORDER.index(ranks[normalized])]
    ]
    return max(available, default=(0, None))[1]


async def sync_athlete_licenses() -> int:
    """Recalculate automatic athlete licenses and return changed row count."""
    result_rows = await Result.filter(final_rank__isnull=False).values(
        "athlete_id", "final_rank"
    )
    licenses_by_athlete: dict[int, list[str | None]] = defaultdict(list)
    for row in result_rows:
        licenses_by_athlete[row["athlete_id"]].append(row["final_rank"])

    athletes = await Athlete.all()
    changed = 0
    for athlete in athletes:
        current = normalize_license(athlete.license)
        if current in MANUAL_LICENSES:
            continue

        desired = highest_automatic_license(
            licenses_by_athlete.get(athlete.id, [])
        )
        if athlete.license != desired:
            old_license = athlete.license
            athlete.license = desired
            await athlete.save(update_fields=["license"])
            changed += 1
            logger.info(
                "Athlete license updated: athlete_id=%s athlete=%s "
                "old_license=%s new_license=%s",
                athlete.id,
                f"{athlete.last_name} {athlete.first_name}",
                old_license,
                desired,
            )
    logger.info("Athlete license synchronization completed: updated=%s", changed)
    return changed
