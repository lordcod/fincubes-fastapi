
from typing import List

from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist

from app.core.deps.redis import get_redis
from app.core.errors import APIError, ErrorCode
from app.core.security.deps.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import Result
from app.repositories.ratings import get_rank
from app.schemas.results.result import (BulkCreateResult,
                                        BulkCreateResultResponse)

router = APIRouter()


@router.post(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=BulkCreateResultResponse,
)
async def bulk_create_results(
    results: List[BulkCreateResult],
    ignore_exception: bool = True,
    redis=Depends(get_redis),
):
    results = []
    errors = []
    competitions = {}

    print("Start parsing", len(results), "athletes")
    count = len(results)
    for index, bulk_request in enumerate(results):
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

                if db_result.result:
                    await get_rank(
                        redis,
                        athlete.gender,
                        result.stroke,
                        result.distance,
                        db_result.result,
                    )
                if db_result.final:
                    await get_rank(
                        redis,
                        athlete.gender,
                        result.stroke,
                        result.distance,
                        db_result.final,
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
