
from typing import List

from fastapi import APIRouter

from app.models.athlete.athlete import Athlete
from app.models.roles.coach_athlete import CoachAthlete
from app.schemas.users.coach import CoachOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=List[CoachOut])
@require_scope('athlete.coaches:read')
async def get_coaches_athlete(athlete_id: int):
    athlete = await Athlete.get(id=athlete_id)
    linked = await CoachAthlete.filter(athlete=athlete).select_related("coach")
    return [await CoachOut.from_tortoise_orm(link.coach) for link in linked]
