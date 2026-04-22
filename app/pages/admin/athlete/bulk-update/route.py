from fastapi import APIRouter, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import (
    BulkAthleteUpdateRequest,
    BulkAthleteUpdateResponse,
)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=BulkAthleteUpdateResponse,
)
@require_scope("athlete:write")
async def bulk_update_athletes(payload: BulkAthleteUpdateRequest):
    if not payload.items:
        return BulkAthleteUpdateResponse(items=[])

    athlete_ids = [item.id for item in payload.items]
    db_athletes = await Athlete.filter(id__in=athlete_ids).all()
    athletes_by_id = {athlete.id: athlete for athlete in db_athletes}

    if len(athletes_by_id) != len(set(athlete_ids)):
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

    updated_fields: set[str] = set()
    updated_athletes = []

    for item in payload.items:
        athlete = athletes_by_id.get(item.id)
        if athlete is None:
            raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

        changes = item.model_dump(exclude={"id"}, exclude_none=True)
        if "birth_year" in changes:
            changes["birth_year"] = str(changes["birth_year"])
        if "gender" in changes:
            changes["gender"] = changes["gender"].upper()

        if changes:
            athlete.update_from_dict(changes)
            updated_fields.update(changes.keys())
        updated_athletes.append(athlete)

    if updated_fields:
        await Athlete.bulk_update(updated_athletes, sorted(updated_fields))

    return BulkAthleteUpdateResponse(items=updated_athletes)
