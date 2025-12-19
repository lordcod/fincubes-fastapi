from typing import List
import json

from fastapi import APIRouter
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import CompetitionResult, CompetitionStage
from app.schemas.results.result import BulkCreateResult, BulkCreateResultResponse
from app.shared.utils.scopes.request import require_scope

BATCH_SIZE = 500

router = APIRouter()


@router.post(
    "/bulk",
    response_model=BulkCreateResultResponse,
)
@require_scope("result:create")
async def bulk_create_results(
    results_data: List[BulkCreateResult],
    ignore_exception: bool = True,
):
    results_objs = []
    stages_objs = []
    errors = []
    competitions = {}

    print("Start parsing", len(results_data), "athletes")

    # Сначала создаем объекты CompetitionResult
    for idx, bulk_request in enumerate(results_data):
        print(
            f"[{idx+1}/{len(results_data)}] Processing athlete_id={bulk_request.athlete_id}")
        try:
            # Получаем или кешируем соревнование
            if bulk_request.competition_id not in competitions:
                try:
                    competition = await Competition.get(id=bulk_request.competition_id)
                except DoesNotExist as exc:
                    raise APIError(ErrorCode.COMPETITION_NOT_FOUND) from exc
                competitions[bulk_request.competition_id] = competition
            else:
                competition = competitions[bulk_request.competition_id]

            # Получаем спортсмена
            try:
                athlete = await Athlete.get(id=bulk_request.athlete_id)
            except DoesNotExist as exc:
                raise APIError(ErrorCode.ATHLETE_NOT_FOUND) from exc

            # Перебираем результаты
            for result_in in bulk_request.results:
                db_result = CompetitionResult(
                    athlete=athlete,
                    competition=competition,
                    **result_in.model_dump(exclude={"stages"})
                )
                results_objs.append(
                    (db_result, getattr(result_in, "metadata", {})))
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

    # Bulk-create результатов
    async with in_transaction() as conn:
        print("Bulk creating CompetitionResult...")
        results_created = await CompetitionResult.bulk_create(
            [r for r, _ in results_objs],
            batch_size=BATCH_SIZE,
            using_db=conn,
            ignore_conflicts=True
        )

        print(f"Created {len(results_created)} CompetitionResult objects")

        # Создаем стейджи
        for (result_obj, metadata) in results_objs:
            attempts = metadata.get("attempts", [])
            total = len(attempts)

            for idx, attempt in enumerate(attempts):
                kind = "HEAT" if idx == 0 else "FINAL" if idx == total - 1 else "SEMIFINAL"
                code = None
                if kind == "SEMIFINAL":
                    code = chr(65 + idx - 1)  # A, B, C ...

                stage_obj = CompetitionStage(
                    result=result_obj,
                    kind=kind,
                    order=idx + 1,
                    code=code,
                    time=attempt,
                    status=getattr(result_obj, "status", "COMPLETED").upper(),
                    place=result_obj.place if idx == total - 1 else None,
                    rank=result_obj.final_rank if idx == total - 1 else None,
                )
                stages_objs.append(stage_obj)

        print(f"Bulk creating {len(stages_objs)} CompetitionStage objects...")
        await CompetitionStage.bulk_create(stages_objs, batch_size=BATCH_SIZE)

    return {"results": results_created, "errors": errors}
