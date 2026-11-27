from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteIn_Pydantic
from app.services.athlete_affiliation import athlete_text_fields
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

    athlete_data = await athlete_text_fields(athlete.model_dump(exclude_unset=True))
    if "birth_year" in athlete_data:
        athlete_data["birth_year"] = str(athlete_data["birth_year"])
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
