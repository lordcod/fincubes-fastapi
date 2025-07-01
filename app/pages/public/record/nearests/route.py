
import random
from datetime import date
from typing import List

from fastapi import APIRouter

from app.models.competition.result import Result
from app.schemas.results.result import Result_Pydantic

router = APIRouter()


@router.get("/", response_model=List[Result_Pydantic])
async def get_records_nearests():
    current_date = date.today()
    current_year = current_date.year
    season = current_year if current_date.month >= 9 else current_year - 1
    season_start = date(season, 9, 1)
    season_end = date(season + 1, 8, 31)

    candidate_ids = await Result.filter(
        record__isnull=False,
        record__not="",
        competition__start_date__gte=season_start,
        competition__end_date__lte=season_end,
    ).limit(50).values_list("id", flat=True)

    if not candidate_ids:
        return []

    selected_ids = random.sample(candidate_ids, min(3, len(candidate_ids)))
    results = await Result.filter(id__in=selected_ids).prefetch_related("competition", "athlete")

    return results
