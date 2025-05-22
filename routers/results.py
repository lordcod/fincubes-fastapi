import contextlib
import random
from fastapi import responses
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Any, List, Optional, Union
from tortoise.exceptions import DoesNotExist
from models.deps import get_redis
from models.models import Athlete, Competition, Result
from schemas.top import RandomTop_Pydantic, Top_Pydantic
from schemas.result import BulkCreateResult, BulkCreateResultResponse, Result_Pydantic, ResultIn_Pydantic
from misc.security import admin_required
from misc.utils import get_rank, get_top_results

router = APIRouter(prefix='/results', tags=['results', 'top'])

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


@router.get("/", response_model=List[Result_Pydantic])
async def get_results(
    athlete_id: Optional[int] = None,
    competition_id: Optional[int] = None,
    stroke: Optional[str] = None,
    distance: Optional[int] = None,
    gender: Optional[str] = None
):
    filters = {}
    if athlete_id:
        filters["athlete_id"] = athlete_id
    if competition_id:
        filters["competition_id"] = competition_id
    if gender:
        filters['athlete__gender'] = gender
    if stroke:
        filters["stroke"] = stroke
    if distance:
        filters["distance"] = distance

    query = Result.filter(**filters)
    return await Result_Pydantic.from_queryset(query)


@router.post("/bulk-create", dependencies=[Depends(admin_required)], response_model=BulkCreateResultResponse)
async def bulk_create_results(results: List[BulkCreateResult], ignore_exception: bool = True, redis=Depends(get_redis)):
    response = []
    errors = []
    competitions = {}

    print('Start parsing', len(results), 'athletes')
    for bulk_request in results:
        print('Athlete start process')
        try:
            if bulk_request.competition_id not in competitions:
                try:
                    competition = await Competition.get(id=bulk_request.competition_id)
                except DoesNotExist:
                    raise HTTPException(
                        status_code=404, detail="Competition not found")
                competitions[bulk_request.competition_id] = competition
            else:
                competition = competitions[bulk_request.competition_id]

            try:
                athlete = await Athlete.get(id=bulk_request.athlete_id)
            except DoesNotExist:
                raise HTTPException(
                    status_code=404, detail="Athlete not found")

            for result in bulk_request.results:
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

                if db_result.result:
                    await get_rank(redis,
                                   athlete.gender,
                                   result.stroke,
                                   result.distance,
                                   db_result.result)
                if db_result.final:
                    await get_rank(redis,
                                   athlete.gender,
                                   result.stroke,
                                   result.distance,
                                   db_result.final)
                response.append(db_result)
        except Exception as exc:
            if not ignore_exception:
                raise
            else:
                errors.append({
                    'exception': True,
                    'name': type(exc).__name__,
                    'description': str(exc),
                    'input': bulk_request
                })

    return {
        'results': response,
        'errors': errors
    }


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

    if result.result:
        await get_rank(redis, athlete.gender, result.stroke, result.distance, result.result)
    if result.final:
        await get_rank(redis, athlete.gender, result.stroke, result.distance, result.final)

    return await Result_Pydantic.from_tortoise_orm(db_result)


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

    return await Result_Pydantic.from_tortoise_orm(db_result)


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
