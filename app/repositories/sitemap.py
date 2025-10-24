import datetime
from tortoise import Tortoise
from app.repositories.sa.sitemap import build_athletes_last_update_query, build_competitions_last_update_query
from app.repositories.sa.utils import compile_query_with_dollar_params


async def get_competitions_last_update():
    query = build_competitions_last_update_query()
    sql, params = compile_query_with_dollar_params(query)
    results = await Tortoise.get_connection(
        "default").execute_query_dict(sql, params)
    for r in results:
        lastmod = r["last_update"]
        if isinstance(lastmod, datetime.datetime):
            r['lastmod'] = lastmod.date()
    return results


async def get_athletes_last_update():
    query = build_athletes_last_update_query()
    sql, params = compile_query_with_dollar_params(query)
    results = await Tortoise.get_connection(
        "default").execute_query_dict(sql, params)
    for r in results:
        lastmod = r["last_update"]
        if isinstance(lastmod, datetime.datetime):
            r['lastmod'] = lastmod.date()
    return results
