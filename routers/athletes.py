from fastapi import APIRouter, Depends, HTTPException
from misc.utils import get_rank
from models.deps import get_redis
from models.models import Athlete, Result
from schemas import Athlete_Pydantic, AthleteIn_Pydantic, UserAthleteResults, UserCompetitionResult
from typing import List
from tortoise.exceptions import DoesNotExist
from tortoise.expressions import Q

from misc.security import admin_required

router = APIRouter(prefix='/athletes')


@router.post("/", dependencies=[Depends(admin_required)], response_model=Athlete_Pydantic)
async def create_athlete(athlete: AthleteIn_Pydantic):
    db_athlete = await Athlete.create(
        last_name=athlete.last_name,
        first_name=athlete.first_name,
        birth_year=athlete.birth_year,
        club=athlete.club,
        license=athlete.license,
        gender=athlete.gender
    )
    return db_athlete


# Роут для получения всех атлетов с фильтрацией
@router.get("/", response_model=List[Athlete_Pydantic])
async def get_athletes(
    query: str = None,
    last_name: str = None,
    first_name: str = None,
    birth_year: int = None,
    club: str = None,
    gender: str = None,
    limit: int = 1000
):
    q_filter = Q()

    if query:
        limit = limit if limit != 1000 else 15

        parts = query.strip().split()
        if len(parts) == 1:
            term = parts[0]
            q_filter |= Q(last_name__icontains=term)
            q_filter |= Q(first_name__icontains=term)
            if term.isdigit():
                q_filter |= Q(birth_year=int(term))

        elif len(parts) == 2:
            a, b = parts
            q_filter |= (Q(last_name__icontains=a) &
                         Q(first_name__icontains=b))
            q_filter |= (Q(last_name__icontains=b) &
                         Q(first_name__icontains=a))

        elif len(parts) == 3:
            a, b, c = parts
            if c.isdigit():
                q_filter |= (Q(last_name__icontains=a) & Q(
                    first_name__icontains=b) & Q(birth_year=int(c)))
                q_filter |= (Q(last_name__icontains=b) & Q(
                    first_name__icontains=a) & Q(birth_year=int(c)))
            else:
                q_filter |= (Q(last_name__icontains=a) & Q(
                    first_name__icontains=f"{b} {c}"))
                q_filter |= (Q(last_name__icontains=b) & Q(
                    first_name__icontains=f"{a} {c}"))

    if last_name:
        q_filter &= Q(last_name__icontains=last_name)
    if first_name:
        q_filter &= Q(first_name__icontains=first_name)
    if birth_year:
        q_filter &= Q(birth_year=birth_year)
    if club:
        q_filter &= Q(club__icontains=club)
    if gender:
        q_filter &= Q(gender=gender)

    athletes = await Athlete.filter(q_filter).limit(limit)
    return athletes

# Роут для получения всех атлетов с фильтрацией


@router.get("/{id}", response_model=AthleteIn_Pydantic)
async def get_athlete(id: int):
    try:
        athlete = await Athlete.get(id=id)
        return athlete
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Athlete not found")

# Роут для обновления атлета


@router.put("/{athlete_id}", dependencies=[Depends(admin_required)], response_model=Athlete_Pydantic)
async def update_athlete(athlete_id: int, athlete: AthleteIn_Pydantic):
    db_athlete = await Athlete.get_or_none(id=athlete_id)
    if not db_athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    db_athlete.last_name = athlete.last_name
    db_athlete.first_name = athlete.first_name
    db_athlete.birth_year = athlete.birth_year
    db_athlete.club = athlete.club
    db_athlete.city = athlete.city
    db_athlete.license = athlete.license
    db_athlete.gender = athlete.gender
    await db_athlete.save()

    return db_athlete


@router.get("/{athlete_id}/performances", response_model=UserAthleteResults)
async def get_athlete_results(athlete_id: int, redis=Depends(get_redis)):
    try:
        athlete = await Athlete.get(id=athlete_id)
        results_query = await Result.filter(athlete=athlete).prefetch_related("competition")
    except DoesNotExist:
        raise HTTPException(
            status_code=404, detail="Athlete or result not found")

    competitions = {}
    best_results = {}
    for result in results_query:
        competition_id = result.competition.id
        if competition_id not in competitions:
            competitions[competition_id] = {
                "id": result.competition.id,
                "date": result.competition.date,
                "start_date": result.competition.start_date,
                "competition": result.competition.name,
                "performances": []
            }
        min_time = (result.final
                    if result.final and result.final <= result.result
                    else result.result)
        if min_time:
            top_rank = await get_rank(
                redis,
                athlete.gender,
                result.stroke,
                result.distance,
                min_time
            )
        else:
            top_rank = None

        performances = {
            "stroke": result.stroke,
            "distance": result.distance,
            "result": result.result,
            "final": result.final,
            "place": result.place,
            "final_rank": result.final_rank,
            "points": result.points,
            "record": result.record,
            "dsq": result.dsq,
            "dsq_final": result.dsq_final,
            "min_time": min_time,
            "top_rank": top_rank
        }

        key = (result.stroke, result.distance)
        best_performance = best_results.get(key)
        if min_time and (best_performance is None or (best_performance['min_time'] > min_time)):
            if best_performance:
                best_performance.pop('best')
            performances['best'] = True
            best_results[key] = performances

        competitions[competition_id]["performances"].append(performances)
    competitions = dict(sorted(competitions.items(),
                        key=lambda item: item[1]['start_date'],
                        reverse=True))
    competition_results = [
        UserCompetitionResult(**comp) for comp in competitions.values()
    ]
    return UserAthleteResults(athlete_id=athlete.id, results=competition_results)
