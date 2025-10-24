from sqlalchemy import (
    select, func
)
from app.repositories.sa.models import athletes, results, competitions


def build_competitions_last_update_query():
    query = (
        select(
            competitions.c.id,
            func.greatest(
                func.date(competitions.c.updated_at),
                func.coalesce(
                    func.max(func.date(results.c.updated_at)),
                    func.date(competitions.c.updated_at)
                )
            ).label("last_update"),
        )
        .select_from(
            competitions.outerjoin(
                results, competitions.c.id == results.c.competition_id
            )
        )
        .group_by(competitions.c.id)
    )
    return query


def build_athletes_last_update_query():
    query = (
        select(
            athletes.c.id,
            func.greatest(
                func.date(athletes.c.updated_at),
                func.coalesce(
                    func.max(func.date(results.c.updated_at)),
                    func.date(athletes.c.updated_at)
                )
            ).label("last_update"),
        )
        .select_from(
            athletes.outerjoin(
                results, athletes.c.id == results.c.athlete_id
            )
        )
        .group_by(athletes.c.id)
    )
    return query
