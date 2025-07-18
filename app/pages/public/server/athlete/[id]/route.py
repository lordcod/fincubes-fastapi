from fastapi import APIRouter
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.competition.result import Result
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteDetailed_Pydantic

router = APIRouter()


@router.get("/", response_model=AthleteDetailed_Pydantic)
async def get_athlete(id: int):
    try:
        athlete = await Athlete.get(id=id)
        athlete_data = await Athlete_Pydantic.from_tortoise_orm(athlete)

        competition_ids = await Result.filter(athlete__id=id).distinct().values_list("competition_id", flat=True)
        competitions_count = len(competition_ids)
        occupied_places_count = await Result.filter(athlete__id=id, place__in={'1', '2', '3'}).count()

        return AthleteDetailed_Pydantic(
            **athlete_data.model_dump(),
            competitions_count=competitions_count,
            occupied_places_count=occupied_places_count
        )
    except DoesNotExist:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
