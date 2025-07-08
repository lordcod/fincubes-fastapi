from fastapi import APIRouter, Depends

from app.core.deps.redis import get_redis
from app.core.protection.secure_request import SecureRequest
from app.repositories.ratings import get_ratings
from app.schemas.results.top import AthleteTopResponse

router = APIRouter()


@router.get("/",
            response_model=AthleteTopResponse,
            dependencies=[Depends(SecureRequest())])
async def get_athlete_top(id: int, redis=Depends(get_redis)):
    return await get_ratings(redis, id)
