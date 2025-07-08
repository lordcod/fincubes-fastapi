
from typing import List

from fastapi import APIRouter, Depends

from app.core.security.deps.permissions import admin_required
from app.models.competition.competition import Competition
from app.schemas.competition.competition import (Competition_Pydantic,
                                                 CompetitionIn_Pydantic)

router = APIRouter(tags=['Admin/Competition'])


@router.post(
    "/", dependencies=[Depends(admin_required)], response_model=Competition_Pydantic
)
async def create_competition(data: CompetitionIn_Pydantic):
    competition = await Competition.create(**data.dict())
    return competition
