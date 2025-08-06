
from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.errors import APIError, ErrorCode

from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import Result
from app.schemas.results.result import Result_Pydantic, ResultIn_Pydantic
from app.shared.clients.scopes.request import require_scope

router = APIRouter()


@router.put(
    "/",
    response_model=Result_Pydantic,
)
@require_scope('result:write')
async def update_result(
    id: int,
    result: ResultIn_Pydantic
):
    db_result = (
        await Result.get(id=id)
        .prefetch_related("competition", "athlete")
    )
    if not db_result:
        raise APIError(ErrorCode.RESULT_NOT_FOUND)
    db_result = await db_result.update_from_dict(result.model_dump())

    return await Result_Pydantic.from_tortoise_orm(db_result)


@router.delete(
    "/",
    status_code=204,
)
@require_scope('result:delete')
async def delete_result(id: int):
    db_result = await Result.get(id=id)
    if not db_result:
        raise APIError(ErrorCode.RESULT_NOT_FOUND)
    await db_result.delete()
