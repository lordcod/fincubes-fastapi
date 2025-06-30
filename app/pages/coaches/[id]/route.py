from fastapi import APIRouter

from app.models.roles.coach import Coach
from app.schemas.users.coach import CoachOut

router = APIRouter()


@router.get("/", response_model=CoachOut)
async def get_coach_from_id(id: int):
    coach = await Coach.get(id=id)
    return await CoachOut.from_tortoise_orm(coach)
