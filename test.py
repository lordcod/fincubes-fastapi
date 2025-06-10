import asyncio
from tortoise import Tortoise
from config import DATABASE_URL
import time
from tortoise import Tortoise
from misc.get_top_results import get_top_results


async def main():
    await Tortoise.init(
        db_url=DATABASE_URL,
        modules={"models": ["models.models"]},
    )
    await Tortoise.generate_schemas()

    # Вызов 1
    start = time.perf_counter()
    results1 = await get_top_results(100, 'BIFINS', 'F', current_season=True, limit=100)
    duration1 = time.perf_counter() - start
    print(f"get_top_results: {duration1:.4f} сек, найдено: {len(results1)}")
    await Tortoise.close_connections()

if __name__ == '__main__':
    asyncio.run(main())
