
from typing import List

from fastapi import APIRouter, Depends


from app.models.competition.competition import Competition
from app.schemas.competition.competition import (Competition_Pydantic,
                                                 CompetitionIn_Pydantic)
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Public/Server/Event'])


@router.get("/", response_model=List[Competition_Pydantic])
@require_scope('competition:read')
async def get_competitions():
    return await Competition.all().order_by("-start_date")
