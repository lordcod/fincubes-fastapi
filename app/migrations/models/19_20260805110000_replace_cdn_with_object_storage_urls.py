from tortoise import BaseDBAsyncClient


CDN_PREFIX = "https://cdn.fincubes.ru/"
STORAGE_PREFIX = "https://storage.yandexcloud.net/fincubes/"


async def upgrade(db: BaseDBAsyncClient) -> str:
    return f"""
        UPDATE "athletes"
        SET "avatar_url" = replace("avatar_url", '{CDN_PREFIX}', '{STORAGE_PREFIX}')
        WHERE "avatar_url" LIKE '{CDN_PREFIX}%';

        UPDATE "region_icons"
        SET "icon_url" = replace("icon_url", '{CDN_PREFIX}', '{STORAGE_PREFIX}')
        WHERE "icon_url" LIKE '{CDN_PREFIX}%';

        UPDATE "competitions"
        SET "links" = replace("links"::text, '{CDN_PREFIX}', '{STORAGE_PREFIX}')::jsonb
        WHERE "links"::text LIKE '%{CDN_PREFIX}%';

        UPDATE "results"
        SET "metadata" = replace("metadata"::text, '{CDN_PREFIX}', '{STORAGE_PREFIX}')::jsonb
        WHERE "metadata" IS NOT NULL
            AND "metadata"::text LIKE '%{CDN_PREFIX}%';

        UPDATE "relay_results"
        SET "metadata" = replace("metadata"::text, '{CDN_PREFIX}', '{STORAGE_PREFIX}')::jsonb
        WHERE "metadata" IS NOT NULL
            AND "metadata"::text LIKE '%{CDN_PREFIX}%';

        UPDATE "relay_legs"
        SET "metadata" = replace("metadata"::text, '{CDN_PREFIX}', '{STORAGE_PREFIX}')::jsonb
        WHERE "metadata" IS NOT NULL
            AND "metadata"::text LIKE '%{CDN_PREFIX}%';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return f"""
        UPDATE "athletes"
        SET "avatar_url" = replace("avatar_url", '{STORAGE_PREFIX}', '{CDN_PREFIX}')
        WHERE "avatar_url" LIKE '{STORAGE_PREFIX}%';

        UPDATE "region_icons"
        SET "icon_url" = replace("icon_url", '{STORAGE_PREFIX}', '{CDN_PREFIX}')
        WHERE "icon_url" LIKE '{STORAGE_PREFIX}%';

        UPDATE "competitions"
        SET "links" = replace("links"::text, '{STORAGE_PREFIX}', '{CDN_PREFIX}')::jsonb
        WHERE "links"::text LIKE '%{STORAGE_PREFIX}%';

        UPDATE "results"
        SET "metadata" = replace("metadata"::text, '{STORAGE_PREFIX}', '{CDN_PREFIX}')::jsonb
        WHERE "metadata" IS NOT NULL
            AND "metadata"::text LIKE '%{STORAGE_PREFIX}%';

        UPDATE "relay_results"
        SET "metadata" = replace("metadata"::text, '{STORAGE_PREFIX}', '{CDN_PREFIX}')::jsonb
        WHERE "metadata" IS NOT NULL
            AND "metadata"::text LIKE '%{STORAGE_PREFIX}%';

        UPDATE "relay_legs"
        SET "metadata" = replace("metadata"::text, '{STORAGE_PREFIX}', '{CDN_PREFIX}')::jsonb
        WHERE "metadata" IS NOT NULL
            AND "metadata"::text LIKE '%{STORAGE_PREFIX}%';
    """
