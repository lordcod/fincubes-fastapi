# migrations/versions/0001_create_competitions_indexes.py
from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> None:
    return """
        -- создаём расширение pg_trgm
        CREATE EXTENSION IF NOT EXISTS pg_trgm;

        -- GIN индекс на name для similarity
        CREATE INDEX IF NOT EXISTS idx_competitions_name_trgm
        ON competitions USING gin (name gin_trgm_ops);

        -- индексы по start_date и end_date
        CREATE INDEX IF NOT EXISTS idx_competitions_start_date
        ON competitions (start_date);

        CREATE INDEX IF NOT EXISTS idx_competitions_end_date
        ON competitions (end_date);

        -- индексы по city и organizer
        CREATE INDEX IF NOT EXISTS idx_competitions_city
        ON competitions (city);

        CREATE INDEX IF NOT EXISTS idx_competitions_organizer
        ON competitions (organizer);
    """


async def downgrade(db: BaseDBAsyncClient) -> None:
    return """
        DROP INDEX IF EXISTS idx_competitions_name_trgm;
        DROP INDEX IF EXISTS idx_competitions_start_date;
        DROP INDEX IF EXISTS idx_competitions_end_date;
        DROP INDEX IF EXISTS idx_competitions_city;
        DROP INDEX IF EXISTS idx_competitions_organizer;
    """
