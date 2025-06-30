
from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import Result
from app.schemas.results.result import Result_Pydantic, ResultIn_Pydantic

router = APIRouter()


@router.put(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=Result_Pydantic,
)
async def update_result(
    competition_id: int, athlete_id: int, result_id: int, result: ResultIn_Pydantic
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

    db_result = (
        await Result.filter(id=result_id, competition=competition, athlete=athlete)
        .first()
        .prefetch_related("competition", "athlete")
    )
    if not db_result:
        raise APIError(ErrorCode.RESULT_NOT_FOUND)
    db_result.stroke = result.stroke
    db_result.distance = result.distance
    db_result.result = result.result
    db_result.final = result.final
    db_result.place = result.place
    db_result.points = result.points
    db_result.record = result.record
    db_result.final_rank = result.final_rank
    db_result.dsq = result.dsq
    db_result.dsq_final = result.dsq_final
    await db_result.save()

    return await Result_Pydantic.from_tortoise_orm(db_result)


@router.delete(
    "/",
    dependencies=[Depends(admin_required)],
    status_code=204,
)
async def delete_result(competition_id: int, athlete_id: int, result_id: int):
    try:
        competition = await Competition.get(id=competition_id)
        athlete = await Athlete.get(id=athlete_id)
    except DoesNotExist as exc:
        raise APIError(
            ErrorCode.ATHLETE_NOT_FOUND
            if exc.model is Athlete
            else ErrorCode.COMPETITION_NOT_FOUND
        )
    db_result = (
        await Result.filter(id=result_id, competition=competition, athlete=athlete)
        .first()
        .prefetch_related("competition", "athlete")
    )
    if not db_result:
        raise APIError(ErrorCode.RESULT_NOT_FOUND)
    await db_result.delete()
