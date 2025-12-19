
from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode

from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import CompetitionStage, CompetitionResult
from app.schemas.results.result import Result_Pydantic, ResultIn_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.put(
    "/",
    response_model=Result_Pydantic,
)
@require_scope("result:write")
async def update_result(id: int, result: ResultIn_Pydantic):
    try:
        db_result = await CompetitionResult.get(id=id)
    except DoesNotExist:
        raise APIError(ErrorCode.RESULT_NOT_FOUND)

    data = result.model_dump(exclude={"stages"})
    db_result.update_from_dict(data)
    await db_result.save(update_fields=list(data.keys()))

    await CompetitionStage.filter(result=db_result).delete()

    stages_objs = []
    for stage_in in getattr(result, "stages", []):
        stages_objs.append(
            CompetitionStage(
                result=db_result,
                kind=stage_in.kind,
                order=stage_in.order,
                time=stage_in.time,
                status=stage_in.status,
                place=stage_in.place,
                rank=stage_in.rank,
                code=getattr(stage_in, "code", None)
            )
        )
    await CompetitionStage.bulk_create(stages_objs)

    return await Result_Pydantic.from_tortoise_orm(db_result)


@router.delete(
    "/",
    status_code=204,
)
@require_scope('result:delete')
async def delete_result(id: int):
    db_result = await CompetitionResult.get(id=id)
    if not db_result:
        raise APIError(ErrorCode.RESULT_NOT_FOUND)
    await db_result.delete()
