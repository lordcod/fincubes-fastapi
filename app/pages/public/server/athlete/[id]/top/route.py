from fastapi import APIRouter, Depends

from app.core.deps.mongodb import get_mongo_collection
from app.repositories.ratings import get_ratings
from app.schemas.results.top import AthleteTopResponse
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=AthleteTopResponse)
@require_scope('athlete.results:read')
async def get_athlete_top(id: int, collection=Depends(get_mongo_collection('ranking'))):
    return await get_ratings(collection, id)
