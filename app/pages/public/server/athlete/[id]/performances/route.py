
from fastapi import APIRouter, Depends

from app.core.deps.redis import get_redis
from app.schemas.athlete.performance import UserAthleteResults
from app.services.athlete_performances import (
    athlete_performances_cache_key,
    build_athlete_performances,
)
from app.shared.cache.redis_compressed import RedisCachePickleCompressed
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=UserAthleteResults)
@require_scope('athlete.results:read')
async def get_athlete_results(id: int, redis=Depends(get_redis)):
    cache_key = athlete_performances_cache_key(id)
    cache = RedisCachePickleCompressed(redis)
    cached = await cache.get(cache_key)
    if cached:
        return cached

    model = (await build_athlete_performances(id)).model_dump()
    await cache.set(cache_key, model, expire_seconds=60 * 15)
    return model
