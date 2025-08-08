
from typing import List

from fastapi import APIRouter

from app.models.athlete.top_athlete import TopAthlete
from app.schemas.athlete.top_athlete import TopAthleteOut
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=List[TopAthleteOut])
@require_scope('athlete.top:read')
async def get_top_athletes():
    query = TopAthlete.all()
    return await TopAthleteOut.from_queryset(query)
