
from datetime import date
from typing import List, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Query


from app.repositories.get_top_results import get_top_results
from app.schemas.results.top import TopResponse, parse_best_full_result
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


class TopRequest(BaseModel):
    distance: int
    stroke: str
    gender: Optional[str] = None

    limit: int = 3
    offset: int = 0

    min_age: Optional[int] = None
    max_age: Optional[int] = None
    categories: Optional[List[str]] = None

    year: Optional[int] = None
    season: Optional[int] = None
    current_season: bool = False

    start_date: Optional[date] = None
    end_date: Optional[date] = None

    courses: Optional[List[str]] = None
    statuses: Optional[List[str]] = None


@router.post("/", response_model=TopResponse)
@require_scope("client.result.top:read")
async def get_top(payload: TopRequest):
    data = payload.model_dump()
    print(data)  # теперь все параметры приходят в теле

    results = await get_top_results(**data)
    return {"results": [parse_best_full_result(res) for res in results]}
