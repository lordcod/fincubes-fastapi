
from typing import List

from fastapi import APIRouter, Depends


from app.models.competition.competition import Competition
from app.schemas.competition.competition import (Competition_Pydantic,
                                                 CompetitionIn_Pydantic)
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Admin/Competition'])


@router.post(
    "/", response_model=Competition_Pydantic
)
@require_scope('competition:create')
async def create_competition(data: CompetitionIn_Pydantic):
    competition = await Competition.create(**data.dict())
    return competition
