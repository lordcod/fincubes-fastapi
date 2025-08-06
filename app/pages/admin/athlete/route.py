
from typing import List

from fastapi import APIRouter, Depends
from tortoise.expressions import Q


from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteIn_Pydantic
from app.shared.clients.scopes.request import require_scope

router = APIRouter(tags=['Admin/Athlete'])


@router.post(
    "/",
    response_model=Athlete_Pydantic
)
@require_scope('athlete:create')
async def create_athlete(athlete: AthleteIn_Pydantic):
    db_athlete = await Athlete.create(**athlete.model_dump())
    return db_athlete
