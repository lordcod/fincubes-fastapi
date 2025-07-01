
from typing import List

from fastapi import APIRouter

from app.models.athlete.top_athlete import TopAthlete
from app.schemas.athlete.top_athlete import TopAthleteOut

router = APIRouter()


@router.get("/", response_model=List[TopAthleteOut])
async def get_top_athletes():
    query = TopAthlete.all()
    return await TopAthleteOut.from_queryset(query)
