from datetime import datetime
from typing import List

from fastapi import APIRouter

from app.models.competition.competition import Competition
from app.schemas.competition.competition import Competition_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=List[Competition_Pydantic])
@require_scope('competition.nearest:read')
async def get_competitions_nearests(limit: int = 3):
    now = datetime.now()
    competitions = (
        Competition.filter(start_date__gte=now).order_by(
            "start_date").limit(limit)
    )
    return await Competition_Pydantic.from_queryset(competitions)
