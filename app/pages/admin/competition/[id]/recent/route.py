from fastapi import APIRouter, Depends


from app.models.competition.competition import Competition
from app.models.competition.recent_event import RecentEvent
from app.schemas.competition.recent_event import RecentEventOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=RecentEventOut,
)
@require_scope('competition.recent:create')
async def add_recent_event(id: int):
    competition = await Competition.get(id=id)
    event = await RecentEvent.create(competition=competition)
    return await RecentEventOut.from_tortoise_orm(event)


@router.delete(
    "/",
    status_code=204,
)
@require_scope('competition.recent:delete')
async def delete_recent_event(id: int):
    recent_event = await RecentEvent.get(id=id)
    await recent_event.delete()
