
from typing import List

from fastapi import APIRouter, Body, Depends

from app.core.security.permissions import admin_required
from app.models.competition.competition import Competition
from app.models.competition.recent_event import RecentEvent
from app.schemas.competition.recent_event import RecentEventOut

router = APIRouter()


@router.get("/", response_model=List[RecentEventOut])
async def get_recent_events():
    query = RecentEvent.all().order_by("-created_at").select_related("competition")
    return await RecentEventOut.from_queryset(query)


@router.post(
    "/",
    dependencies=[Depends(admin_required)],
    response_model=RecentEventOut,
)
async def add_recent_event(competition_id=Body(embed=True)):
    competition = await Competition.get(id=competition_id)
    event = await RecentEvent.create(competition=competition)
    return await RecentEventOut.from_tortoise_orm(event)
