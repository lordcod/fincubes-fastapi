from fastapi import APIRouter, Body, Depends
from tortoise.exceptions import DoesNotExist

from app.core.deps.redis import get_redis
from app.core.errors import APIError, ErrorCode

from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import CompetitionResult
from app.schemas.results.result import Result_Pydantic, ResultIn_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=['Admin/Result'])


@router.post(
    "/",
    response_model=Result_Pydantic,
)
@require_scope('result:create')
async def create_result(
    result: ResultIn_Pydantic,
    competition_id: int = Body(embed=True),
    athlete_id: int = Body(embed=True),
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

    db_result = await CompetitionResult.create(
        athlete=athlete,
        competition=competition,
        **result.model_dump()
    )
    return await Result_Pydantic.from_tortoise_orm(db_result)
