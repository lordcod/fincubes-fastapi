
from typing import List, Optional

from fastapi import APIRouter, Depends


from app.models.competition.competition import Competition
from app.schemas.competition.competition import (Competition_Pydantic,
                                                 CompetitionIn_Pydantic)
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=['Public/Server/Event'])


@router.get("/", response_model=List[Competition_Pydantic])
@require_scope('competition:read')
async def get_competitions(limit: Optional[int] = None, offset: Optional[int] = None):
    query = Competition.all().order_by("-start_date")

    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
        query = query.offset(offset)
    return await query
