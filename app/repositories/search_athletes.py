from typing import Optional
from tortoise import Tortoise
from app.repositories.sa.search_athlete import build_athlete_search_query
from app.repositories.sa.utils import compile_query_with_dollar_params


async def search_athletes(search: str, limit: Optional[int]):
    query = build_athlete_search_query(search, limit)
    sql, params = compile_query_with_dollar_params(query)
    results = await Tortoise.get_connection(
        "default").execute_query_dict(
            sql, params)
    return results
