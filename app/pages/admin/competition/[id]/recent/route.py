from datetime import datetime
from fastapi import APIRouter, Depends


from app.models.competition.competition import Competition
from app.schemas.competition.competition import Competition_Pydantic
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=Competition_Pydantic,
)
@require_scope('competition.recent:create')
async def add_recent_event(id: int):
    competition = await Competition.get(id=id)
    competition.last_processed_at = datetime.now()
    await competition.save()
    return await Competition_Pydantic.from_tortoise_orm(competition)


@router.delete(
    "/",
    status_code=204,
)
@require_scope('competition.recent:delete')
async def delete_recent_event(id: int):
    competition = await Competition.get(id=id)
    competition.last_processed_at = None
    await competition.save()
