from math import dist
from typing import List
from email_validator import ALLOW_QUOTED_LOCAL
from fastapi import APIRouter, HTTPException, Request, status, Depends
from tortoise.exceptions import DoesNotExist
from models.models import Competition, Distance
from schemas.distance import Distance_Pydantic, DistanceCreateUpdateIn_Pydantic, DistanceOrderUpdate_Pydantic
from utils.security import admin_required

router = APIRouter(prefix='/competitions/{competition_id}/distances')

# Получить все дистанции для конкретного соревнования


@router.get("/", response_model=list[Distance_Pydantic])
async def get_distances(competition_id: int):
    try:
        competition = await Competition.get(id=competition_id)
        distances = await competition.distances.all().order_by('order')
        return distances
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Competition not found")

# Получить дистанцию по id для конкретного соревнования


@router.get("/{distance_id}", response_model=Distance_Pydantic)
async def get_distance(competition_id: int, distance_id: int):
    try:
        distance = await Distance.filter(id=distance_id, competition_id=competition_id).first()
        if not distance:
            raise HTTPException(status_code=404, detail="Distance not found")
        return distance
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail="Competition or Distance not found")

# Добавить новую дистанцию в конкретное соревнование


@router.post("/", dependencies=[Depends(admin_required)], response_model=Distance_Pydantic)
async def create_distance(competition_id: int, distance: DistanceCreateUpdateIn_Pydantic):
    try:
        kwargs = distance.dict()
        competition = await Competition.get(id=competition_id)
        new_distance = await Distance.create(**kwargs, competition=competition)
        return new_distance
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Competition not found")


@router.put("/bulk-update", dependencies=[Depends(admin_required)], response_model=List[Distance_Pydantic])
async def bulk_update_distances(request: Request, competition_id: int, distances: List[DistanceOrderUpdate_Pydantic]):
    try:
        existing_distances = await Distance.filter(id__in=[d.id for d in distances], competition_id=competition_id).all()
        if len(existing_distances) != len(distances):
            raise HTTPException(
                status_code=404, detail="Some distances not found")

        dists = {}
        for dist in existing_distances:
            dists[dist.id] = dist

        new = []
        for update in distances:
            dist = dists[update.id]
            dist.order = update.order
            new.append(dist)
        await Distance.bulk_update(new, ['order'])

        return new
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Competition not found")


@router.put("/{distance_id}", dependencies=[Depends(admin_required)], response_model=Distance_Pydantic)
async def update_distance(competition_id: int, distance_id: int, distance: DistanceCreateUpdateIn_Pydantic):
    try:
        existing_distance = await Distance.filter(id=distance_id, competition_id=competition_id).first()

        if not existing_distance:
            raise HTTPException(status_code=404, detail="Distance not found")

        existing_distance.stroke = distance.stroke
        existing_distance.distance = distance.distance
        existing_distance.category = distance.category
        existing_distance.order = distance.order
        existing_distance.gender = distance.gender

        # Сохраняем изменения
        await existing_distance.save()

        return existing_distance
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Competition not found")

# Удалить дистанцию для конкретного соревнования


@router.delete("/{distance_id}", dependencies=[Depends(admin_required)], status_code=status.HTTP_205_RESET_CONTENT)
async def delete_distance(competition_id: int, distance_id: int):
    try:
        distance = await Distance.filter(id=distance_id, competition_id=competition_id).first()
        if distance:
            await distance.delete()
        else:
            raise HTTPException(status_code=404, detail="Distance not found")
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Competition not found")
