from typing import Any, Optional
from sqlalchemy import (
    CTE, Table, Integer, select, and_, func, cast, text
)
from sqlalchemy.sql.functions import dense_rank
from datetime import date
from sqlalchemy.dialects import postgresql
from app.repositories.sa.models import athletes, results, competitions
from app.repositories.sa.utils import prepare_columns, label_columns


def build_top_results_query(
    distance: Optional[int] = None,
    stroke: Optional[str] = None,
    gender: Optional[str] = None,
    limit: Optional[int] = None,

    offset: Optional[int] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    season: Optional[int] = None,
    current_season: Optional[bool] = False,
):
    current_date = date.today()
    current_year = current_date.year

    if current_season:
        season = current_year if current_date.month >= 9 else current_year - 1

    season_start = date(season, 9, 1) if season else None
    season_end = date(season + 1, 8, 31) if season else None

    base_filters = [results.c.resolved_time.isnot(None)]
    if stroke:
        base_filters.append(results.c.stroke == stroke)
    if distance:
        base_filters.append(results.c.distance == distance)
    if gender:
        base_filters.append(athletes.c.gender == gender)

    best_results_filters = list(base_filters)
    if season_start and season_end:
        best_results_filters.extend([
            competitions.c.start_date >= season_start,
            competitions.c.end_date <= season_end
        ])

    best_results_subq = (
        select(
            results.c.athlete_id,
            results.c.stroke,
            results.c.distance,
            func.min(results.c.resolved_time).label("resolved_time")
        )
        .select_from(
            results
            .join(athletes, athletes.c.id == results.c.athlete_id)
            .join(competitions, competitions.c.id == results.c.competition_id)
        )
        .where(and_(*best_results_filters))
        .group_by(
            results.c.athlete_id,
            results.c.stroke,
            results.c.distance,
        )
        .subquery("best_results")
    )

    query = (
        select(
            *label_columns(results, "result"),
            *label_columns(athletes, "athlete"),
            *label_columns(competitions, "competition"),
            dense_rank().over(
                partition_by=[
                    results.c.stroke,
                    results.c.distance,
                    athletes.c.gender
                ],
                order_by=results.c.resolved_time
            ).label("row_num")
        )
        .select_from(
            results
            .join(athletes, athletes.c.id == results.c.athlete_id)
            .join(competitions, competitions.c.id == results.c.competition_id)
            .join(best_results_subq, and_(
                results.c.athlete_id == best_results_subq.c.athlete_id,
                results.c.stroke == best_results_subq.c.stroke,
                results.c.distance == best_results_subq.c.distance,
                results.c.resolved_time == best_results_subq.c.resolved_time,
            ))
        )
        .where(and_(*base_filters))
    )

    if min_age is not None or max_age is not None:
        birth_min = current_year - max_age if max_age else None
        birth_max = current_year - min_age if min_age else None

        if min_age and max_age:
            query = query.where(
                cast(athletes.c.birth_year, Integer).between(
                    birth_min, birth_max)
            )
        elif min_age:
            query = query.where(
                cast(athletes.c.birth_year, Integer) <= birth_max)
        elif max_age:
            query = query.where(
                cast(athletes.c.birth_year, Integer) >= birth_min)

    query = query.order_by(text("row_num"))
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    return query
