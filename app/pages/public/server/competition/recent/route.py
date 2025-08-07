
from typing import List

from fastapi import APIRouter, Body, Depends


from app.models.competition.competition import Competition
from app.models.competition.recent_event import RecentEvent
from app.schemas.competition.recent_event import RecentEventOut
from app.shared.clients.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=List[RecentEventOut])
@require_scope('competition.recent:read')
async def get_recent_events():
    query = RecentEvent.all().order_by("-created_at").select_related("competition")
    return await RecentEventOut.from_queryset(query)
