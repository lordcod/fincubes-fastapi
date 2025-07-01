
from typing import List

from fastapi import APIRouter, Body, Depends

from app.core.security.permissions import admin_required
from app.models.athlete.athlete import Athlete
from app.models.athlete.top_athlete import TopAthlete
from app.schemas.athlete.top_athlete import TopAthleteOut

router = APIRouter()


@router.get("/", response_model=List[TopAthleteOut])
async def get_top_athletes():
    query = TopAthlete.all()
    return await TopAthleteOut.from_queryset(query)
