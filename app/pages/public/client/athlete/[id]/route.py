from fastapi import APIRouter
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import AthleteIn_Pydantic

router = APIRouter()


@router.get("/", response_model=AthleteIn_Pydantic)
async def get_athlete(id: int):
    try:
        athlete = await Athlete.get(id=id)
        return athlete
    except DoesNotExist:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
