
from fastapi import APIRouter, Depends


from app.models.athlete.athlete import Athlete
from app.models.athlete.top_athlete import TopAthlete
from app.schemas.athlete.top_athlete import TopAthleteOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=TopAthleteOut,
)
@require_scope('athlete.top:create')
async def add_top_athlete(id: int):
    athlete = await Athlete.get(id=id)
    top = await TopAthlete.create(athlete=athlete)
    return await TopAthleteOut.from_tortoise_orm(top)


@router.delete(
    "/",
    status_code=204,
)
@require_scope('athlete.top:delete')
async def delete_top_athlete(id: int):
    athlete = await Athlete.get(id=id)
    top_athlete = await TopAthlete.filter(athlete=athlete).first()
    if top_athlete is None:
        return
    await top_athlete.delete()
