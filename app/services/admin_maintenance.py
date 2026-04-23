from typing import Optional

from pydantic import BaseModel, Field
from tortoise.functions import Count

from app.core.security.hashing import hash_password
from app.models import Athlete, Distance, Result, User


class AthleteSnapshot(BaseModel):
    id: int
    last_name: str
    first_name: str
    birth_year: str
    gender: str


class CompetitionResultCount(BaseModel):
    competition_id: int
    results: int


class MaintenanceOperationResult(BaseModel):
    operation: str
    dry_run: bool
    affected: int = 0
    messages: list[str] = Field(default_factory=list)


class TransferResultsResult(MaintenanceOperationResult):
    from_athlete: Optional[AthleteSnapshot] = None
    to_athlete: Optional[AthleteSnapshot] = None
    competition_id: Optional[int] = None
    competitions: list[CompetitionResultCount] = Field(default_factory=list)
    remaining_source_results: Optional[int] = None
    deleted_source_athlete: bool = False


class ChangePasswordResult(MaintenanceOperationResult):
    user_id: int
    changed: bool = False


def snapshot_athlete(athlete: Athlete) -> AthleteSnapshot:
    return AthleteSnapshot(
        id=athlete.id,
        last_name=athlete.last_name,
        first_name=athlete.first_name,
        birth_year=athlete.birth_year,
        gender=athlete.gender,
    )


async def transfer_results(
    from_athlete_id: int,
    to_athlete_id: int,
    competition_id: Optional[int] = None,
    apply: bool = False,
    delete_empty_source: bool = False,
) -> TransferResultsResult:
    response = TransferResultsResult(
        operation="transfer_results",
        dry_run=not apply,
        competition_id=competition_id,
    )

    if from_athlete_id == to_athlete_id:
        response.messages.append("from_athlete_id and to_athlete_id must be different")
        return response

    athlete_from = await Athlete.get_or_none(id=from_athlete_id)
    if not athlete_from:
        response.messages.append(f"Source athlete not found: {from_athlete_id}")
        return response
    response.from_athlete = snapshot_athlete(athlete_from)

    athlete_to = await Athlete.get_or_none(id=to_athlete_id)
    if not athlete_to:
        response.messages.append(f"Target athlete not found: {to_athlete_id}")
        return response
    response.to_athlete = snapshot_athlete(athlete_to)

    query = Result.filter(athlete_id=from_athlete_id)
    if competition_id is not None:
        query = query.filter(competition_id=competition_id)

    results = await query.order_by("competition_id", "id").all()
    response.affected = len(results)
    if not results:
        response.messages.append("No results to transfer.")
        return response

    competition_counts: dict[int, int] = {}
    for result in results:
        competition_counts[result.competition_id] = competition_counts.get(result.competition_id, 0) + 1
    response.competitions = [
        CompetitionResultCount(competition_id=comp_id, results=count)
        for comp_id, count in sorted(competition_counts.items())
    ]

    if not apply:
        response.messages.append("Dry-run only. Re-run with apply=true to move these results.")
        return response

    for result in results:
        result.athlete_id = to_athlete_id
    await Result.bulk_update(results, ["athlete_id"])

    response.messages.append(
        f"Moved {len(results)} result(s) from athlete #{from_athlete_id} to #{to_athlete_id}."
    )

    remaining = await Result.filter(athlete_id=from_athlete_id).count()
    response.remaining_source_results = remaining
    response.messages.append(f"Source athlete remaining results: {remaining}")

    if delete_empty_source and remaining == 0:
        await athlete_from.delete()
        response.deleted_source_athlete = True
        response.messages.append(f"Deleted empty source athlete #{from_athlete_id}.")
    elif delete_empty_source:
        response.messages.append("Source athlete was not deleted because it still has results.")

    return response


async def clear_results(competition_id: int, apply: bool = False) -> MaintenanceOperationResult:
    count = await Result.filter(competition_id=competition_id).count()
    response = MaintenanceOperationResult(
        operation="clear_results",
        dry_run=not apply,
        affected=count,
    )

    if not apply:
        response.messages.append("Dry-run only. Re-run with apply=true to delete these results.")
        return response

    deleted = await Result.filter(competition_id=competition_id).delete()
    response.affected = deleted
    response.messages.append(f"Deleted results: {deleted}")
    return response


async def clear_distances(competition_id: int, apply: bool = False) -> MaintenanceOperationResult:
    count = await Distance.filter(competition_id=competition_id).count()
    response = MaintenanceOperationResult(
        operation="clear_distances",
        dry_run=not apply,
        affected=count,
    )

    if not apply:
        response.messages.append("Dry-run only. Re-run with apply=true to delete these distances.")
        return response

    deleted = await Distance.filter(competition_id=competition_id).delete()
    response.affected = deleted
    response.messages.append(f"Deleted distances: {deleted}")
    return response


async def clear_empty_athletes(apply: bool = False) -> MaintenanceOperationResult:
    athletes_without_results = await Athlete.annotate(results_count=Count("results")).filter(results_count=0)
    count = len(athletes_without_results)
    response = MaintenanceOperationResult(
        operation="clear_empty_athletes",
        dry_run=not apply,
        affected=count,
    )

    if not apply:
        response.messages.append("Dry-run only. Re-run with apply=true to delete these athletes.")
        return response

    for athlete in athletes_without_results:
        await athlete.delete()

    response.messages.append(f"Deleted athletes without results: {count}")
    return response


async def change_password(user_id: int, new_password: str, apply: bool = False) -> ChangePasswordResult:
    response = ChangePasswordResult(
        operation="change_password",
        dry_run=not apply,
        user_id=user_id,
    )

    user = await User.filter(id=user_id).first()
    if not user:
        response.messages.append(f"User not found: {user_id}")
        return response

    response.affected = 1
    if not apply:
        response.messages.append("Dry-run only. Re-run with apply=true to change this password.")
        return response

    user.hashed_password = hash_password(new_password)
    await user.save(update_fields=["hashed_password", "updated_at"])
    response.changed = True
    response.messages.append(f"Password changed for user #{user_id}.")
    return response
