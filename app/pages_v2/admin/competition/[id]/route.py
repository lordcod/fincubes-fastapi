
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


@router.put(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=Competition_Pydantic,
)
async def update_competition(id: int, competition: CompetitionIn_Pydantic):
    comp = await Competition.get_or_none(id=id)
    if not comp:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
    await comp.update_from_dict(competition.dict()).save()
    return comp


@router.delete(
    "/", dependencies=[Depends(admin_required)], status_code=204
)
async def delete_competition(id: int):
    competition = await Competition.get_or_none(id=id)
    if not competition:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
    await competition.delete()
    return
