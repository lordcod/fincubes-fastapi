
from typing import List

from fastapi import APIRouter

from app.models.competition.result import Result
from app.schemas.results.result import Result_Pydantic

router = APIRouter()


@router.get("/", response_model=List[Result_Pydantic])
async def get_records_nearests():
    results = (
        await Result.filter(record__isnull=False, record__not="")
        .order_by("-competition__end_date")
        .prefetch_related("competition", "athlete")
        .limit(3)
    )
    return results
