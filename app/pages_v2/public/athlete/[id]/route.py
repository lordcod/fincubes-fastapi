from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteIn_Pydantic

router = APIRouter()


@router.get("/", response_model=AthleteIn_Pydantic)
async def get_athlete(id: int):
    try:
        athlete = await Athlete.get(id=id)
        return athlete
    except DoesNotExist:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
