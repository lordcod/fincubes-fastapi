from typing import Optional
from sqlalchemy import select, func, or_, and_, String
from app.repositories.sa.models import athletes


def build_athlete_search_query(user_input: str, limit: Optional[int] = None, similarity_threshold: float = 0.3):
    words = user_input.strip().split()
    if not words:
        return select(athletes).limit(0)

    conds = []

    def sim(col, w):
        return func.similarity(func.cast(col, String), w)

    if len(words) == 1:
        w = words[0]
        conds.append(sim(athletes.c.first_name, w) > similarity_threshold)
        conds.append(sim(athletes.c.last_name, w) > similarity_threshold)
    elif len(words) >= 2:
        w1, w2 = words[:2]
        conds.append(and_(sim(athletes.c.last_name, w1) > similarity_threshold,
                          sim(athletes.c.first_name, w2) > similarity_threshold))
        conds.append(and_(sim(athletes.c.last_name, w2) > similarity_threshold,
                          sim(athletes.c.first_name, w1) > similarity_threshold))

    total_similarity = (
        func.coalesce(sim(athletes.c.first_name, words[0]), 0) +
        func.coalesce(sim(athletes.c.last_name,  words[0]), 0) +
        func.coalesce(sim(athletes.c.first_name, words[1] if len(words) > 1 else ""), 0) +
        func.coalesce(sim(athletes.c.last_name,
                      words[1] if len(words) > 1 else ""), 0)
    ).label("total_similarity")

    where_expr = or_(*conds, total_similarity > similarity_threshold)

    stmt = (
        select(athletes)
        .where(where_expr)
        .order_by(total_similarity.desc())
    )

    if limit is not None:
        stmt = stmt.limit(limit)

    return stmt
