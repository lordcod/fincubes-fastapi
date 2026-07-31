from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "locations";

        DROP INDEX IF EXISTS "idx_location_objects_club_id";
        DROP INDEX IF EXISTS "idx_location_objects_city_id";
        DROP INDEX IF EXISTS "idx_location_objects_region_id";

        ALTER TABLE "location_objects"
            DROP COLUMN IF EXISTS "club_id",
            DROP COLUMN IF EXISTS "city_id",
            DROP COLUMN IF EXISTS "region_id";
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "location_objects"
            ADD COLUMN IF NOT EXISTS "club_id" UUID,
            ADD COLUMN IF NOT EXISTS "city_id" UUID,
            ADD COLUMN IF NOT EXISTS "region_id" UUID;

        CREATE TABLE IF NOT EXISTS "locations" (
            "id" SERIAL PRIMARY KEY,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "alias" VARCHAR(512) NOT NULL,
            "athlete_id" INT NOT NULL REFERENCES "athletes" ("id") ON DELETE CASCADE,
            "location_object_id" UUID NOT NULL REFERENCES "location_objects" ("id") ON DELETE RESTRICT,
            UNIQUE ("athlete_id", "location_object_id", "alias")
        );
    """
