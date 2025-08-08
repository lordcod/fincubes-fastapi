from fastapi import APIRouter

from app.models.roles.coach import Coach
from app.schemas.users.coach import CoachOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=['Internal/Coach'])


@router.get("/", response_model=CoachOut)
@require_scope('coach:read')
async def get_coach_from_id(id: int):
    coach = await Coach.get(id=id)
    return await CoachOut.from_tortoise_orm(coach)
