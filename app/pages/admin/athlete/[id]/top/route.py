
from fastapi import APIRouter, Depends


from app.models.athlete.athlete import Athlete
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=Athlete_Pydantic,
)
@require_scope('athlete.top:create')
async def add_top_athlete(id: int):
    athlete = await Athlete.get(id=id)
    athlete.is_top = True
    await athlete.save()
    return await Athlete_Pydantic.from_tortoise_orm(athlete)


@router.delete(
    "/",
    status_code=204,
)
@require_scope('athlete.top:delete')
async def delete_top_athlete(id: int):
    athlete = await Athlete.get(id=id)
    athlete.is_top = False
    await athlete.save()
