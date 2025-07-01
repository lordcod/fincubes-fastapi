
from typing import Optional

from fastapi import APIRouter

from app.repositories.get_top_results import get_top_results
from app.schemas.results.top import TopResponse, parse_best_full_result

router = APIRouter()


@router.get("/", response_model=TopResponse)
async def get_top(
    distance: int,
    stroke: str,
    gender: Optional[str] = None,
    limit: int = 3,
    offset: int = 0,
    min_age: int = None,
    max_age: int = None,
    season: Optional[int] = None,
    current_season: Optional[bool] = False,
):
    results = await get_top_results(
        distance,
        stroke,
        gender,
        limit,
        offset,
        min_age,
        max_age,
        season,
        current_season,
    )
    return {"results": [parse_best_full_result(res) for res in results]}
