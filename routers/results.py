import random
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Any, List, Optional
from tortoise.exceptions import DoesNotExist
from models.deps import get_redis
from models.models import Athlete, Competition, Result
from schemas import RandomTop_Pydantic, Result_Pydantic, ResultIn_Pydantic, Top_Pydantic
from misc.security import admin_required
from misc.utils import get_rank, get_top_results

router = APIRouter(prefix='/results')

swim_styles = [
    {'stroke': 'APNEA', 'distance': 50},

    {'stroke': 'BIFINS', 'distance': 50},
    {'stroke': 'BIFINS', 'distance': 100},
    {'stroke': 'BIFINS', 'distance': 200},
    {'stroke': 'BIFINS', 'distance': 400},

    {'stroke': 'IMMERSION', 'distance': 100},
    {'stroke': 'IMMERSION', 'distance': 400},

    {'stroke': 'SURFACE', 'distance': 50},
    {'stroke': 'SURFACE', 'distance': 100},
    {'stroke': 'SURFACE', 'distance': 200},
    {'stroke': 'SURFACE', 'distance': 400},
    {'stroke': 'SURFACE', 'distance': 800},
    {'stroke': 'SURFACE', 'distance': 1500},
]


@router.get("/records/nearests", response_model=List[Result_Pydantic])
async def get_records_nearests():
    results = await Result.filter(
        record__isnull=False, record__not="").order_by('-competition__end_date').prefetch_related("competition", "athlete").limit(3)
    return results


@router.get('/top/random', response_model=RandomTop_Pydantic)
async def get_random_top():
    item = random.choice(swim_styles)
    return item


@router.get('/top/', response_model=Top_Pydantic)
async def get_top(
    distance: int,
    stroke: str,
    gender: Optional[str] = None,
    limit: int = 3,
    offset: int = 0,
    min_age: int = None,
    max_age: int = None,
    competition_ids: list[int] = None,
    season: Optional[int] = None,
    current_season: Optional[bool] = False
):
    results = await get_top_results(
        distance,
        stroke,
        gender,
        limit,
        offset,
        min_age,
        max_age,
        competition_ids,
        season,
        current_season
    )
    return Top_Pydantic(
        distance=distance,
        stroke=stroke,
        results=results
    )


# Роут для получения всех результатов с фильтрацией


@router.get("/", response_model=List[Result_Pydantic])
async def get_results(
    athlete_id: Optional[int] = None,
    competition_id: Optional[int] = None,
    stroke: Optional[str] = None,
    distance_id: Optional[int] = None,
):
    filters = {}
    if athlete_id:
        filters["athlete_id"] = athlete_id
    if competition_id:
        filters["competition_id"] = competition_id
    if stroke:
        filters["stroke"] = stroke
    if distance_id:
        filters["distance_id"] = distance_id

    results = await Result.filter(**filters).prefetch_related(
        "competition",
        "athlete"
    )
    return results


@router.post("/{competition_id}/{athlete_id}", dependencies=[Depends(admin_required)], response_model=Result_Pydantic)
async def create_result(competition_id: int, athlete_id: int, result: ResultIn_Pydantic, redis=Depends(get_redis)):
    try:
        competition = await Competition.get(id=competition_id)
        athlete = await Athlete.get(id=athlete_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail="Competition or athlete not found")

    db_result = await Result.create(
        athlete=athlete,
        competition=competition,
        stroke=result.stroke,
        distance=result.distance,
        result=result.result,
        final=result.final,
        place=result.place,
        points=result.points,
        record=result.record,
        final_rank=result.final_rank,
        dsq=result.dsq,
        dsq_final=result.dsq_final,
    )

    await get_rank(redis, athlete.gender, result.stroke, result.distance, result.result)
    if result.final:
        await get_rank(redis, athlete.gender, result.stroke, result.distance, result.final)

    return db_result


# Роут для обновления существующего результата
@router.put("/{competition_id}/{athlete_id}/{result_id}", dependencies=[Depends(admin_required)], response_model=Result_Pydantic)
async def update_result(competition_id: int, athlete_id: int, result_id: int, result: ResultIn_Pydantic):
    try:
        competition = await Competition.get(id=competition_id)
        athlete = await Athlete.get(id=athlete_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail="Competition or athlete not found")

    db_result = await Result.filter(id=result_id, competition=competition, athlete=athlete).first().prefetch_related(
        "competition",
        "athlete"
    )
    if not db_result:
        raise HTTPException(status_code=404, detail="Result not found")

    db_result.stroke = result.stroke
    db_result.distance = result.distance
    db_result.result = result.result
    db_result.final = result.final
    db_result.place = result.place
    db_result.points = result.points
    db_result.record = result.record
    db_result.final_rank = result.final_rank
    db_result.dsq = result.dsq
    db_result.dsq_final = result.dsq_final
    await db_result.save()

    return db_result


@router.delete("/{competition_id}/{athlete_id}/{result_id}", dependencies=[Depends(admin_required)], status_code=204)
async def delete_result(competition_id: int, athlete_id: int, result_id: int):
    try:
        competition = await Competition.get(id=competition_id)
        athlete = await Athlete.get(id=athlete_id)
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail="Competition or athlete not found")

    db_result = await Result.filter(id=result_id, competition=competition, athlete=athlete).first().prefetch_related(
        "competition",
        "athlete"
    )
    if not db_result:
        raise HTTPException(status_code=404, detail="Result not found")
    await db_result.delete()
