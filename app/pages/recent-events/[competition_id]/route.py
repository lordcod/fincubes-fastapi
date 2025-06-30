from fastapi import APIRouter, Depends

from app.core.security.permissions import admin_required
from app.models.competition.recent_event import RecentEvent

router = APIRouter()


@router.delete(
    "/",
    dependencies=[Depends(admin_required)],
    status_code=204,
)
async def delete_recent_event(competition_id: int):
    recent_event = await RecentEvent.get(id=competition_id)
    await recent_event.delete()
