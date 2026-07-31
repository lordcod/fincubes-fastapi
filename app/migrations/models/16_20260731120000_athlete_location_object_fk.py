from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "athletes"
            ADD COLUMN IF NOT EXISTS "location_object_id" UUID
                REFERENCES "location_objects" ("id") ON DELETE SET NULL;

        UPDATE "athletes" AS athlete
        SET "location_object_id" = location_object."id"
        FROM "location_objects" AS location_object
        WHERE athlete."location_object_id" IS NULL
            AND COALESCE(athlete."club", '') = COALESCE(location_object."club", '')
            AND COALESCE(athlete."city", '') = COALESCE(location_object."city", '')
            AND COALESCE(athlete."region", '') = COALESCE(location_object."region", '');

        CREATE INDEX IF NOT EXISTS "idx_athletes_location_object"
            ON "athletes" ("location_object_id");

        ALTER TABLE "athletes"
            DROP COLUMN IF EXISTS "club",
            DROP COLUMN IF EXISTS "city",
            DROP COLUMN IF EXISTS "region";
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "athletes"
            ADD COLUMN IF NOT EXISTS "club" VARCHAR(255),
            ADD COLUMN IF NOT EXISTS "city" VARCHAR(255),
            ADD COLUMN IF NOT EXISTS "region" VARCHAR(255);

        UPDATE "athletes" AS athlete
        SET
            "club" = location_object."club",
            "city" = location_object."city",
            "region" = location_object."region"
        FROM "location_objects" AS location_object
        WHERE athlete."location_object_id" = location_object."id";

        DROP INDEX IF EXISTS "idx_athletes_location_object";

        ALTER TABLE "athletes"
            DROP COLUMN IF EXISTS "location_object_id";
    """
