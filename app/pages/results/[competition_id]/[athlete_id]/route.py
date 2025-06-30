from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.deps.redis import get_redis
from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import Result
from app.repositories.ratings import get_rank
from app.schemas.results.result import Result_Pydantic, ResultIn_Pydantic

router = APIRouter()


@router.post(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=Result_Pydantic,
)
async def create_result(
    competition_id: int,
    athlete_id: int,
    result: ResultIn_Pydantic,
    redis=Depends(get_redis),
):
    try:
        competition = await Competition.get(id=competition_id)
        athlete = await Athlete.get(id=athlete_id)
    except DoesNotExist as exc:
        raise APIError(
            ErrorCode.ATHLETE_NOT_FOUND
            if exc.model is Athlete
            else ErrorCode.COMPETITION_NOT_FOUND
        ) from exc

    db_result = await Result.create(
        athlete=athlete,
        competition=competition,
        stroke=result.stroke,
        distance=result.distance,
        result=result.result,
        final=result.final,
        place=result.place,
        points=result.points,
        record=result.record,
        final_rank=result.final_rank,
        dsq=result.dsq,
        dsq_final=result.dsq_final,
    )

    if result.result:
        await get_rank(
            redis, athlete.gender, result.stroke, result.distance, result.result
        )
    if result.final:
        await get_rank(
            redis, athlete.gender, result.stroke, result.distance, result.final
        )

    return await Result_Pydantic.from_tortoise_orm(db_result)
