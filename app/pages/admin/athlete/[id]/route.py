from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode

from app.models.athlete.athlete import Athlete
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

    db_athlete.update_from_dict(athlete.model_dump())
    await db_athlete.save()

    return db_athlete


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
