from fastapi import APIRouter, Depends

from app.core.deps.redis import get_redis
from app.repositories.ratings import get_ratings
from app.schemas.results.top import AthleteTopResponse
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=AthleteTopResponse)
@require_scope('athlete.results:read')
async def get_athlete_top(id: int, redis=Depends(get_redis)):
    return await get_ratings(redis, id)
