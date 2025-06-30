
from fastapi import APIRouter, Depends

from app.core.security.permissions import admin_required
from app.models.athlete.top_athlete import TopAthlete

router = APIRouter()


@router.delete(
    "/",
    dependencies=[Depends(admin_required)],
    status_code=204,
)
async def delete_top_athlete(athlete_id: int):
    top_athlete = await TopAthlete.get(id=athlete_id)
    await top_athlete.delete()
