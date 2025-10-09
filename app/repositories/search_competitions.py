from typing import Optional
from tortoise import Tortoise
from app.repositories.sa.search_competition import build_competition_search_query
from app.repositories.sa.utils import compile_query_with_dollar_params


async def search_competitions(
    user_input: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    city: Optional[str] = None,
    organizer: Optional[str] = None,
    limit: Optional[int] = None,
):
    query = build_competition_search_query(
        user_input=user_input,
        start_date=start_date,
        end_date=end_date,
        city=city,
        organizer=organizer,
        limit=limit,
    )
    sql, params = compile_query_with_dollar_params(query)
    results = await Tortoise.get_connection("default").execute_query_dict(sql, params)
    return results
