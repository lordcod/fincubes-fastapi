from typing import List

from fastapi import APIRouter, Body, Depends
from models.models import Athlete, Competition, TopAthlete, RecentEvent
from schemas.home import TopAthleteIn, TopAthleteOut, RecentEventIn, RecentEventOut
from misc.security import admin_required

router = APIRouter(tags=['top', 'recent'])


@router.get("/top-athletes", response_model=List[TopAthleteOut])
async def get_top_athletes():
    query = TopAthlete.all()
    return await TopAthleteOut.from_queryset(query)


@router.post("/top-athletes", dependencies=[Depends(admin_required)], response_model=TopAthleteOut)
async def add_top_athlete(athlete_id: int = Body(embed=True)):
    athlete = await Athlete.get(id=athlete_id)
    top = await TopAthlete.create(athlete=athlete)
    return await TopAthleteOut.from_tortoise_orm(top)


@router.delete("/top-athletes/{athlete_id}", dependencies=[Depends(admin_required)], status_code=204)
async def delete_top_athlete(athlete_id: int):
    top_athlete = await TopAthlete.get(id=athlete_id)
    await top_athlete.delete()


@router.get("/recent-events", response_model=List[RecentEventOut])
async def get_recent_events():
    query = RecentEvent.all().order_by("-created_at").select_related("competition")
    return await RecentEventOut.from_queryset(query)


@router.post("/recent-events", dependencies=[Depends(admin_required)], response_model=RecentEventOut)
async def add_recent_event(competition_id=Body(embed=True)):
    competition = await Competition.get(id=competition_id)
    event = await RecentEvent.create(competition=competition)
    return await RecentEventOut.from_tortoise_orm(event)


@router.delete("/recent-events/{competition_id}", dependencies=[Depends(admin_required)], status_code=204)
async def delete_recent_event(competition_id: int):
    recent_event = await RecentEvent.get(id=competition_id)
    await recent_event.delete()
