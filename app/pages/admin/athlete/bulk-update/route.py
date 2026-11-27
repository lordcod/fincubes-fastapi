from fastapi import APIRouter, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.bulk import (
    BulkAthleteUpdateRequest,
    BulkAthleteUpdateResponse,
)
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.services.athlete_affiliation import athlete_text_fields
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

        changes = await athlete_text_fields(item.model_dump(exclude={"id"}, exclude_unset=True))
        # Nullable affiliation/license fields may be explicitly cleared.
        # Preserve the historical no-op behavior for null required identity fields.
        for field in ("last_name", "first_name", "birth_year", "gender"):
            if field in changes and changes[field] is None:
                changes.pop(field)
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

    return BulkAthleteUpdateResponse(
        items=[
            await Athlete_Pydantic.from_tortoise_orm(athlete)
            for athlete in updated_athletes
        ]
    )
