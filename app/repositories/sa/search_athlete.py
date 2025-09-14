from typing import Optional
from sqlalchemy import select, func, or_, and_, String
from app.repositories.sa.models import athletes


def build_athlete_search_query(user_input: str, limit: Optional[int], similarity_threshold: float = 0.3):
    words = user_input.split()

    conds = []

    def sim_gt(col, w):
        return func.similarity(func.cast(col, String), w) > similarity_threshold

    if len(words) == 1:
        w = words[0]
        conds.append(sim_gt(athletes.c.first_name, w))
        conds.append(sim_gt(athletes.c.last_name, w))
    elif len(words) == 2:
        w1, w2 = words

        conds.append(and_(sim_gt(athletes.c.last_name, w1),
                          sim_gt(athletes.c.first_name, w2)))
        conds.append(and_(sim_gt(athletes.c.last_name, w2),
                          sim_gt(athletes.c.first_name, w1)))

    max_similarity = func.greatest(
        func.coalesce(func.similarity(
            func.cast(athletes.c.first_name, String), words[0]), 0),
        func.coalesce(func.similarity(
            func.cast(athletes.c.last_name,  String), words[0]), 0),
        func.coalesce(func.similarity(func.cast(athletes.c.first_name, String),
                      words[1] if len(words) > 1 else ""), 0),
        func.coalesce(func.similarity(func.cast(athletes.c.last_name, String),
                      words[1] if len(words) > 1 else ""), 0),
    ).label("max_similarity")

    where_expr = or_(*conds)

    stmt = (
        select(athletes)
        .where(where_expr)
        .order_by(max_similarity.desc())
    )

    if limit is not None:
        stmt = stmt.limit(limit)

    return stmt
