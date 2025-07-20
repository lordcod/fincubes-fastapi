from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.deps.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteIn_Pydantic

router = APIRouter()


@router.put(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=Athlete_Pydantic,
)
async def update_athlete(id: int, athlete: AthleteIn_Pydantic):
    db_athlete = await Athlete.get_or_none(id=id)
    if not db_athlete:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

    db_athlete.last_name = athlete.last_name
    db_athlete.first_name = athlete.first_name
    db_athlete.birth_year = athlete.birth_year
    db_athlete.club = athlete.club
    db_athlete.city = athlete.city
    db_athlete.license = athlete.license
    db_athlete.gender = athlete.gender
    await db_athlete.save()

    return db_athlete


@router.delete(
    "/",
    dependencies=[Depends(admin_required)],
    status_code=204
)
async def delete_athlete(id: int):
    db_athlete = await Athlete.get_or_none(id=id)
    if not db_athlete:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
    await db_athlete.delete()
