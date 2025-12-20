from typing import Any, List, Optional
from sqlalchemy import (
    CTE, Table, Integer, select, and_, func, cast, text, or_
)
from sqlalchemy.sql.functions import dense_rank
from datetime import date
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import array
from app.repositories.sa.models import athletes, results, competitions
from app.repositories.sa.utils import prepare_columns, label_columns
from app.shared.utils.metadata import categories as CATEGORY_CONFIG
CATEGORY_INDEX = {c["id"]: c for c in CATEGORY_CONFIG}


def build_top_results_query(
    distance: Optional[int] = None,
    stroke: Optional[str] = None,
    gender: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    categories: Optional[List[str]] = None,
    year: Optional[int] = None,
    season: Optional[int] = None,
    current_season: Optional[bool] = False,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    courses: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
):
    current_date = date.today()
    current_year = current_date.year

    if current_season:
        season = current_year if current_date.month >= 9 else current_year - 1

    year_start = date(year, 1, 1) if year else None
    year_end = date(year, 12, 31) if year else None
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
    if year_start and year_end:
        best_results_filters.extend([
            competitions.c.start_date >= year_start,
            competitions.c.end_date <= year_end
        ])
    if start_date:
        best_results_filters.append(competitions.c.start_date >= start_date)
    if end_date:
        best_results_filters.append(competitions.c.end_date <= end_date)

    if courses:
        courses_clean = [c for c in courses if c]
        if courses_clean:
            best_results_filters.append(
                competitions.c.course.in_(tuple(courses_clean)))

    if statuses:
        statuses_clean = [s for s in statuses if s]
        if statuses_clean:
            best_results_filters.append(
                competitions.c.status.in_(tuple(statuses_clean)))

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

    # ✅ безопасная фильтрация по категориям
    if categories:
        age_conditions = []
        for cat_id in categories:
            cfg = CATEGORY_INDEX.get(cat_id)
            if not cfg:
                continue

            min_cat_age = cfg["min_age"]
            max_cat_age = cfg["max_age"]

            # если категория абсолютная — пропускаем фильтр по возрасту
            if min_cat_age is None and max_cat_age is None:
                age_conditions = []
                break

            birth_min = current_year - max_cat_age if max_cat_age is not None else None
            birth_max = current_year - min_cat_age if min_cat_age is not None else None
            col = cast(athletes.c.birth_year, Integer)

            if birth_min is not None and birth_max is not None:
                age_conditions.append(col.between(birth_min, birth_max))
            elif birth_min is not None:
                age_conditions.append(col >= birth_min)
            elif birth_max is not None:
                age_conditions.append(col <= birth_max)

        if age_conditions:
            query = query.where(or_(*age_conditions))

    # ✅ отдельные min/max_age параметры
    if min_age is not None:
        birth_max = current_year - min_age
        query = query.where(cast(athletes.c.birth_year, Integer) <= birth_max)
    if max_age is not None:
        birth_min = current_year - max_age
        query = query.where(cast(athletes.c.birth_year, Integer) >= birth_min)

    query = query.order_by(text("row_num"))
    if offset:
        query = query.offset(offset)
    if limit:
        query = query.limit(limit)

    return query
