from fastapi import APIRouter, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.location.location_object import LocationObject
from app.schemas.athlete.bulk import (
    BulkAthleteUpdateRequest,
    BulkAthleteUpdateResponse,
)
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.services.location_catalog import resolve_athlete_location_object
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
        alias = changes.pop("alias", None)
        club = changes.pop("club", None)
        city = changes.pop("city", None)
        region = changes.pop("region", None)
        location_object_id = changes.pop("location_object_id", None)

        if location_object_id is not None:
            location_exists = await LocationObject.filter(id=location_object_id).exists()
            if not location_exists:
                raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)
            changes["location_object_id"] = location_object_id
        elif any(value is not None for value in (alias, club, city, region)):
            location = await resolve_athlete_location_object(
                alias=alias,
                club=club,
                city=city,
                region=region,
            )
            changes["location_object_id"] = location.id if location else None

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
