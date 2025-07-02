
from typing import List

from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from app.core.errors import APIError, ErrorCode
from app.core.security.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteIn_Pydantic
from app.schemas.competition.competition import (Competition_Pydantic,
                                                 CompetitionIn_Pydantic)

router = APIRouter()


@router.get("/", response_model=Competition_Pydantic)
async def get_competition(competition_id: int):
    comp = await Competition.get_or_none(id=competition_id)
    if not comp:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
    return comp
