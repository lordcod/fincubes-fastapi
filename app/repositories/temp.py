import json
from typing import Any, Optional, Union, get_args
from sqlalchemy import (
    CTE, Table, Column, Integer, String, Date, Float, select, case, and_, or_, func, literal_column, cast, text, MetaData
)
from sqlalchemy.sql import alias
from sqlalchemy.sql.functions import dense_rank
from sqlalchemy.sql.expression import over
from sqlalchemy.ext.asyncio import AsyncEngine
from datetime import date
from sqlalchemy.dialects import sqlite, mysql, postgresql

from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import Result
from app.sql.utils import tortoise_model_to_sqlalchemy_table


metadata = MetaData()
results = tortoise_model_to_sqlalchemy_table(Result)
athletes = tortoise_model_to_sqlalchemy_table(Athlete)
competitions = tortoise_model_to_sqlalchemy_table(Competition)


def label_columns(table_or_cte: Table | CTE, prefix: str, include: Optional[set[str]] = None, exclude: Optional[set[str]] = None):
    columns = []
    for col in table_or_cte.c:
        if include and col.name not in include:
            continue
        if exclude and col.name in exclude:
            continue
        columns.append(col.label(f"{prefix}_{col.name}"))
    return columns


def prepare_columns(base_model, fields: dict[str, Any], prefix: str):
    filtered = {}
    prefix_with_underscore = f'{prefix}_'
    for name, value in fields.items():
        if name.startswith(prefix_with_underscore):
            trimmed = name[len(prefix_with_underscore):]
            filtered[trimmed] = value
    return base_model(**filtered)


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

    filters = [results.c.resolved_time != None]
    if stroke:
        filters.append(results.c.stroke == stroke)
    if distance:
        filters.append(results.c.distance == distance)
    if gender:
        filters.append(athletes.c.gender == gender)

    best_results_subq = (
        select(
            results.c.athlete_id,
            results.c.stroke,
            results.c.distance,
            func.min(results.c.resolved_time).label("resolved_time")
        )
        .select_from(
            results.join(athletes, athletes.c.id == results.c.athlete_id)
        )
        .where(and_(*filters))
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
        .where(and_(*filters))
    )

    filters2 = []
    if min_age is not None or max_age is not None:
        birth_min = current_year - max_age if max_age else None
        birth_max = current_year - min_age if min_age else None

        if min_age and max_age:
            filters2.append(cast(athletes.c.birth_year,
                            Integer).between(birth_min, birth_max))
        elif min_age:
            filters2.append(cast(athletes.c.birth_year, Integer) <= birth_max)
        elif max_age:
            filters2.append(cast(athletes.c.birth_year, Integer) >= birth_min)

    if season_start and season_end:
        filters2.extend([
            competitions.c.start_date >= season_start,
            competitions.c.end_date <= season_end
        ])

    if filters2:
        query = query.where(and_(*filters2))

    query = query.order_by(text("row_num"))
    if offset:
        query = query.where(text("row_num > :offset")).params(offset=offset)
    if limit:
        query = query.limit(limit)

    return query


def compile_query_with_dollar_params(query):
    compiled = query.compile(dialect=postgresql.dialect(), compile_kwargs={
                             "literal_binds": False})
    sql = str(compiled)
    params = compiled.params
    param_map = {name: f"${i+1}" for i, name in enumerate(params.keys())}

    for name, dollar in param_map.items():
        sql = sql.replace(f"%({name})s", dollar)

    param_values = params.values()
    return sql, list(param_values)
