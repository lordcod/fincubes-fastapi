from typing import List

from fastapi import APIRouter, Depends
from models.models import Athlete, Competition, TopAthlete, RecentEvent
from schemas.home import TopAthleteIn, TopAthleteOut, RecentEventIn, RecentEventOut
from misc.security import admin_required

router = APIRouter()


@router.get("/top-athletes", response_model=List[TopAthleteOut])
async def get_top_athletes():
    return await TopAthlete.all().prefetch_related("athlete")


@router.post("/top-athletes", dependencies=[Depends(admin_required)], response_model=TopAthleteOut)
async def add_top_athlete(data: TopAthleteIn):
    athlete = await Athlete.get(id=data.athlete_id)
    return await TopAthlete.create(athlete=athlete)


@router.delete("/top-athletes/{athlete_id}", dependencies=[Depends(admin_required)], status_code=204)
async def delete_top_athlete(athlete_id: int):
    top_athlete = await TopAthlete.get(id=athlete_id)
    await top_athlete.delete()


@router.get("/recent-events", response_model=List[RecentEventOut])
async def get_recent_events():
    return await RecentEvent.all().order_by("-created_at").prefetch_related("competition")


@router.post("/recent-events", dependencies=[Depends(admin_required)], response_model=RecentEventOut)
async def add_recent_event(data: RecentEventIn):
    competition = await Competition.get(id=data.competition_id)
    return await RecentEvent.create(competition=competition)


@router.delete("/recent-events/{competition_id}", dependencies=[Depends(admin_required)], status_code=204)
async def delete_recent_event(competition_id: int):
    recent_event = await RecentEvent.get(id=competition_id)
    await recent_event.delete()
