
from typing import List

from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.deps.redis import get_redis
from app.core.errors import APIError, ErrorCode

from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import Result
from app.schemas.results.result import (BulkCreateResult,
                                        BulkCreateResultResponse)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=BulkCreateResultResponse,
)
@require_scope('result:create')
async def bulk_create_results(
    results_data: List[BulkCreateResult],
    ignore_exception: bool = True
):
    results = []
    errors = []
    competitions = {}

    print("Start parsing", len(results_data), "athletes")
    count = len(results_data)
    for index, bulk_request in enumerate(results_data):
        print(f"[{index}/{count}] Athlete start process")
        try:
            if bulk_request.competition_id not in competitions:
                try:
                    competition = await Competition.get(id=bulk_request.competition_id)
                except DoesNotExist as exc:
                    raise APIError(ErrorCode.COMPETITION_NOT_FOUND) from exc
                competitions[bulk_request.competition_id] = competition
            else:
                competition = competitions[bulk_request.competition_id]

            try:
                athlete = await Athlete.get(id=bulk_request.athlete_id)
            except DoesNotExist as exc:
                raise APIError(ErrorCode.ATHLETE_NOT_FOUND) from exc

            for result in bulk_request.results:
                db_result = Result(
                    athlete=athlete,
                    competition=competition,
                    **result.model_dump()
                )
                results.append(db_result)
        except Exception as exc:
            if not ignore_exception:
                raise
            else:
                errors.append(
                    {
                        "exception": True,
                        "name": type(exc).__name__,
                        "description": str(exc),
                        "input": bulk_request,
                    }
                )

    response = await Result.bulk_create(results)
    return {"results": response, "errors": errors}
