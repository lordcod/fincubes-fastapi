
from typing import List

from fastapi import APIRouter

from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=List[Athlete_Pydantic])
@require_scope('athlete.top:read')
async def get_top_athletes(limit: int = 3):
    query = Athlete.filter(is_top=True).limit(limit)
    return await Athlete_Pydantic.from_queryset(query)
