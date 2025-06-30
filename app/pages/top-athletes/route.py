
from typing import List

from fastapi import APIRouter, Body, Depends

from app.core.security.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.models.athlete.top_athlete import TopAthlete
from app.schemas.athlete.top_athlete import TopAthleteOut

router = APIRouter()


@router.get("/", response_model=List[TopAthleteOut])
async def get_top_athletes():
    query = TopAthlete.all()
    return await TopAthleteOut.from_queryset(query)


@router.post(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=TopAthleteOut,
)
async def add_top_athlete(athlete_id: int = Body(embed=True)):
    athlete = await Athlete.get(id=athlete_id)
    top = await TopAthlete.create(athlete=athlete)
    return await TopAthleteOut.from_tortoise_orm(top)
