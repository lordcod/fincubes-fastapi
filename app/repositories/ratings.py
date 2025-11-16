import logging
from collections import defaultdict
from datetime import time
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from app.repositories.get_top_results import get_top_results
from app.schemas.results.top import parse_best_full_result
from app.shared.cache.redis_compressed import RedisCachePickleCompressed
from app.shared.utils.metadata import categories
from pymongo import UpdateOne

_log = logging.getLogger(__name__)

BATCH_SIZE = 1000


def as_duration(result: time):
    return (
        result.hour * 60 * 60
        + result.minute * 60
        + result.second
        + ((result.microsecond // 1000) / 1000)
    )


async def update_ratings(collection: AsyncIOMotorCollection):
    _log.info("Starting athlete rankings update")

    athlete_results = defaultdict(lambda: defaultdict(list))

    for season in [True, False]:
        season_str = 'current_season' if season else 'global'
        for category in categories:
            _log.debug("Processing category '%s' for season '%s'",
                       category['name'], season_str)

            results = await get_top_results(min_age=category['min_age'],
                                            max_age=category['max_age'],
                                            current_season=season)
            results = [parse_best_full_result(res) for res in results]
            for top in results:
                athlete_results[top.athlete.id][
                    season_str + ':' + category['id']].append(
                    top.model_dump(mode='json')
                )
    _log.info("Collected results for %d athletes", len(athlete_results))

    operations = [
        UpdateOne(
            {"_id": athlete_id},
            {"$set": {"rankings": dict(rankings)}},
            upsert=True
        )
        for athlete_id, rankings in athlete_results.items()
    ]

    await collection.bulk_write(operations)
    _log.info("Saved ranking results for athletes")


async def get_ratings(collection: AsyncIOMotorCollection, id: int):
    doc = await collection.find_one({"_id": id})
    return doc["rankings"] if doc else {}
