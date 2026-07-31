from fastapi import APIRouter

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=dict)
@require_scope("athlete:read")
async def get_athlete_locations(athlete_id: int):
    athlete = await Athlete.get_or_none(id=athlete_id)
    if athlete is None:
        raise APIError(ErrorCode.ATHLETE_NOT_FOUND)
    return {
        "athlete_id": athlete.id,
        "club": athlete.club,
        "city": athlete.city,
        "region": athlete.region,
        "location_links": [],
    }
