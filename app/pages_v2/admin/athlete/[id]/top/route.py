
from fastapi import APIRouter, Depends

from app.core.security.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.models.athlete.top_athlete import TopAthlete
from app.schemas.athlete.top_athlete import TopAthleteOut

router = APIRouter()


@router.post(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=TopAthleteOut,
)
async def add_top_athlete(id: int):
    athlete = await Athlete.get(id=id)
    top = await TopAthlete.create(athlete=athlete)
    return await TopAthleteOut.from_tortoise_orm(top)


@router.delete(
    "/",
    dependencies=[Depends(admin_required)],
    status_code=204,
)
async def delete_top_athlete(id: int):
    top_athlete = await TopAthlete.get(id=id)
    await top_athlete.delete()
