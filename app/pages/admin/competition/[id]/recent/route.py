from fastapi import APIRouter, Depends

from app.core.security.deps.permissions import admin_required
from app.models.competition.competition import Competition
from app.models.competition.recent_event import RecentEvent
from app.schemas.competition.recent_event import RecentEventOut

router = APIRouter()


@router.post(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=RecentEventOut,
)
async def add_recent_event(id: int):
    competition = await Competition.get(id=id)
    event = await RecentEvent.create(competition=competition)
    return await RecentEventOut.from_tortoise_orm(event)


@router.delete(
    "/",
    dependencies=[Depends(admin_required)],
    status_code=204,
)
async def delete_recent_event(id: int):
    recent_event = await RecentEvent.get(id=id)
    await recent_event.delete()
