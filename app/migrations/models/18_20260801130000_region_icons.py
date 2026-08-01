from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "region_icons" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "id" SERIAL NOT NULL PRIMARY KEY,
            "name" VARCHAR(255) NOT NULL UNIQUE,
            "format" VARCHAR(16) NOT NULL,
            "icon_url" VARCHAR(512) NOT NULL
        );

        CREATE INDEX IF NOT EXISTS "idx_region_icons_name"
            ON "region_icons" ("name");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "region_icons";
    """
