
from typing import List

from fastapi import APIRouter, Depends
from tortoise.expressions import Q


from app.models.athlete.athlete import Athlete
from app.repositories.search_athletes import search_athletes
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=['Public/Client/Athlete'])


@router.get("/", response_model=List[Athlete_Pydantic])
@require_scope('client.athlete:read')
async def get_athletes(
    query: str,
    limit: int = 15,
):
    return await search_athletes(query, limit)
