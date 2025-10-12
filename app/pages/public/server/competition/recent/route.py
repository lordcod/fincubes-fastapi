
from typing import List

from fastapi import APIRouter


from app.models.competition.competition import Competition
from app.schemas.competition.competition import Competition_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.get("/", response_model=List[Competition_Pydantic])
@require_scope('competition.recent:read')
async def get_recent_events(limit: int = 3):
    competitions = (
        Competition.filter(last_processed_at__isnull=False).order_by(
            "-last_processed_at").limit(limit)
    )
    return await Competition_Pydantic.from_queryset(competitions)
