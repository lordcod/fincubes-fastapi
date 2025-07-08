
from typing import List

from fastapi import APIRouter, Depends
from tortoise.expressions import Q

from app.core.security.deps.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic, AthleteIn_Pydantic

router = APIRouter(tags=['Admin/Athlete'])


@router.post(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=Athlete_Pydantic
)
async def create_athlete(athlete: AthleteIn_Pydantic):
    db_athlete = await Athlete.create(**athlete.model_dump())
    return db_athlete
