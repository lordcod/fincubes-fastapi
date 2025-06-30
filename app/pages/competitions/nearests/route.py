from datetime import datetime
from typing import List

from fastapi import APIRouter

from app.models.competition.competition import Competition
from app.schemas.competition.competition import Competition_Pydantic

router = APIRouter()


@router.get("/", response_model=List[Competition_Pydantic])
async def get_competitions_nearests():
    # now = timezone.now().date()
    now = datetime.now()
    competitions = (
        await Competition.filter(start_date__gte=now).order_by("start_date").limit(3)
    )
    return competitions
