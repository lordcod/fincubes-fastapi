from typing import Optional
from sqlalchemy import case, select, func, or_, and_, String
from app.repositories.sa.models import athletes


def build_athlete_search_query(user_input: str, limit: Optional[int], similarity_threshold: float = 0.3):
    words = user_input.strip().split()

    # The client starts searching from three characters, but keep the API
    # safe as well: an empty/too short query should never produce a broad DB
    # scan or an invalid ``or_()`` expression.
    if len("".join(words)) < 3:
        return select(athletes).where(False).limit(0)

    name_columns = (
        athletes.c.first_name,
        athletes.c.last_name,
    )

    def matches(col, word):
        value = func.cast(col, String)
        return or_(
            # Covers normal typing and partial first/last names. ILIKE is
            # case-insensitive for Cyrillic in PostgreSQL.
            value.ilike(f"%{word}%"),
            func.similarity(value, word) > similarity_threshold,
        )

    if len(words) == 1:
        where_expr = or_(*(matches(column, words[0]) for column in name_columns))
    elif len(words) == 2:
        first_word, second_word = words
        # Prefer the natural ``last name + first name`` order, while also
        # accepting ``first name + last name``.
        where_expr = or_(
            and_(matches(athletes.c.last_name, first_word),
                 matches(athletes.c.first_name, second_word)),
            and_(matches(athletes.c.last_name, second_word),
                 matches(athletes.c.first_name, first_word)),
        )
    else:
        # More than two tokens are uncommon, but every entered token should
        # still participate in the search instead of silently returning no
        # results because the old implementation only handled two tokens.
        where_expr = and_(*[
            or_(*(matches(column, word) for column in name_columns))
            for word in words
        ])

    def relevance(column, word):
        value = func.cast(column, String)
        return case(
            (value.ilike(word), 4),
            (value.ilike(f"{word}%"), 3),
            (value.ilike(f"%{word}%"), 2),
            (func.similarity(value, word) > similarity_threshold, 1),
            else_=0,
        )

    relevance_score = sum(
        func.greatest(*(relevance(column, word) for column in name_columns))
        for word in words
    ).label("relevance_score")

    stmt = (
        select(athletes)
        .where(where_expr)
        .order_by(relevance_score.desc())
    )

    if limit is not None:
        stmt = stmt.limit(limit)

    return stmt
