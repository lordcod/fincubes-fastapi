
from tortoise import timezone
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models.models import Competition
from schemas.competition import Competition_Pydantic, CompetitionIn_Pydantic
from misc.security import admin_required

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("/nearests", response_model=List[Competition_Pydantic])
async def get_competitions_nearests():
    now = timezone.now().date()
    competitions = await Competition.filter(
        start_date__gte=now
    ).order_by('start_date').limit(3)
    return competitions


@router.get("/", response_model=List[Competition_Pydantic])
async def get_competitions():
    return await Competition.all().order_by("-start_date")


@router.get("/{competition_id}", response_model=Competition_Pydantic)
async def get_competition(competition_id: int):
    comp = await Competition.get_or_none(id=competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return comp


@router.post("/", dependencies=[Depends(admin_required)], response_model=Competition_Pydantic)
async def create_competition(data: CompetitionIn_Pydantic):
    # Создаём новое соревнование на основе переданных данных и возвращаем его с ID
    competition = await Competition.create(**data.dict())
    return competition


# PUT update existing competition
@router.put("/{competition_id}", dependencies=[Depends(admin_required)], response_model=Competition_Pydantic)
async def update_competition(competition_id: int, competition: CompetitionIn_Pydantic):
    comp = await Competition.get_or_none(id=competition_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    await comp.update_from_dict(competition.dict()).save()
    return comp


@router.delete("/{competition_id}", dependencies=[Depends(admin_required)], status_code=204)
async def delete_competition(competition_id: int):
    competition = await Competition.get_or_none(id=competition_id)
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")
    await competition.delete()
    return
