from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode

from app.models.athlete.athlete import Athlete
from app.models.location.location_object import LocationObject
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteIn_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.put(
    "/",
    response_model=Athlete_Pydantic,
)
@require_scope('athlete:write')
async def update_athlete(id: int, athlete: AthleteIn_Pydantic):
    db_athlete = await Athlete.get_or_none(id=id)
    if not db_athlete:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

    athlete_data = athlete.model_dump()
    location_object_id = athlete_data.pop("location_object_id", None)
    if location_object_id is not None:
        location_exists = await LocationObject.filter(id=location_object_id).exists()
        if not location_exists:
            raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)
    athlete_data["birth_year"] = str(athlete_data["birth_year"])
    athlete_data["location_object_id"] = location_object_id
    db_athlete.update_from_dict(athlete_data)
    await db_athlete.save()

    return await Athlete_Pydantic.from_tortoise_orm(db_athlete)


@router.delete(
    "/",
    status_code=204
)
@require_scope('athlete:delete')
async def delete_athlete(id: int):
    db_athlete = await Athlete.get_or_none(id=id)
    if not db_athlete:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
    await db_athlete.delete()
