
from typing import List

from fastapi import APIRouter, Depends
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from app.core.errors import APIError, ErrorCode

from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteIn_Pydantic
from app.schemas.competition.competition import (Competition_Pydantic,
                                                 CompetitionIn_Pydantic)
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.put(
    "/",
    response_model=Competition_Pydantic,
)
@require_scope('competition:write')
async def update_competition(id: int, competition: CompetitionIn_Pydantic):
    comp = await Competition.get_or_none(id=id)
    if not comp:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
    await comp.update_from_dict(competition.dict()).save()
    return comp


@router.delete(
    "/", status_code=204
)
@require_scope('competition:delete')
async def delete_competition(id: int):
    competition = await Competition.get_or_none(id=id)
    if not competition:
        raise APIError(ErrorCode.COMPETITION_NOT_FOUND)
    await competition.delete()
    return
