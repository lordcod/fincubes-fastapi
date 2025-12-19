from tortoise.transactions import in_transaction
from tortoise.backends.base.client import BaseDBAsyncClient


async def ensure_resolved_time_column(conn: BaseDBAsyncClient):
    search_sql = """
    SELECT column_name, is_generated
    FROM information_schema.columns
    WHERE table_name = 'results' AND column_name = 'resolved_time';
    """
    drop_sql = "ALTER TABLE results DROP COLUMN resolved_time;"
    add_sql = """
    ALTER TABLE results
    ADD COLUMN resolved_time timetz GENERATED ALWAYS AS (
        CASE
            WHEN result IS NULL AND final IS NULL THEN NULL
            WHEN result IS NULL THEN final
            WHEN final IS NULL THEN result
            ELSE LEAST(result, final)
        END
    ) STORED;
    """
    result = await conn.execute_query_dict(search_sql)
    if result:
        is_generated = result[0].get('is_generated')
        if is_generated != 'ALWAYS':
            await conn.execute_script(drop_sql)
            await conn.execute_script(add_sql)
    else:
        await conn.execute_script(add_sql)


async def ensure_pg_trgm_extension(conn: BaseDBAsyncClient):
    await conn.execute_script("CREATE EXTENSION IF NOT EXISTS pg_trgm;")


async def ensure_indexes(conn: BaseDBAsyncClient):
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_athletes_first_name_trgm ON athletes USING gin (first_name gin_trgm_ops);",
        "CREATE INDEX IF NOT EXISTS idx_athletes_last_name_trgm ON athletes USING gin (last_name gin_trgm_ops);",

        # "CREATE INDEX IF NOT EXISTS idx_results_effective_search ON results (stroke, distance, athlete_id, result, final);",
        "CREATE INDEX IF NOT EXISTS idx_athletes_gender ON athletes (id, gender);",
        # "CREATE INDEX IF NOT EXISTS idx_results_not_null_result ON results (stroke, distance, athlete_id, result, final) WHERE result IS NOT NULL OR final IS NOT NULL;"
    ]

    for sql in indexes:
        await conn.execute_script(sql)


async def init_postgres():
    async with in_transaction() as conn:
        # await ensure_resolved_time_column(conn)

        await ensure_pg_trgm_extension(conn)

        await ensure_indexes(conn)
