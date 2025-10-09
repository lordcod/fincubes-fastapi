from typing import Optional
from sqlalchemy import select, func, String, and_
from app.repositories.sa.models import competitions


def build_competition_search_query(
    user_input: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    city: Optional[str] = None,
    organizer: Optional[str] = None,
    limit: Optional[int] = None,
    similarity_threshold: float = 0.3,
):
    conds = []

    if user_input:
        # similarity
        sim_expr = func.similarity(
            func.cast(competitions.c.name, String), user_input)
        conds.append(sim_expr > similarity_threshold)

        # подстрочное совпадение для коротких слов
        conds.append(competitions.c.name.ilike(f"%{user_input}%"))

        # сортировка
        total_similarity = func.coalesce(sim_expr, 0).label("total_similarity")
    else:
        total_similarity = func.literal(0).label("total_similarity")

    if start_date:
        conds.append(competitions.c.start_date >= start_date)
    if end_date:
        conds.append(competitions.c.end_date <= end_date)
    if city:
        conds.append(competitions.c.city.ilike(f"%{city}%"))
    if organizer:
        conds.append(competitions.c.organizer.ilike(f"%{organizer}%"))

    where_expr = and_(*conds) if conds else True

    stmt = (
        select(competitions)
        .where(where_expr)
        .order_by(total_similarity.desc())
    )

    if limit:
        stmt = stmt.limit(limit)

    return stmt
