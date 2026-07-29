from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE EXTENSION IF NOT EXISTS pg_trgm;

        DROP TABLE IF EXISTS "review_decision";
        DROP TABLE IF EXISTS "review_item";
        DROP TABLE IF EXISTS "review_session";

        CREATE TABLE IF NOT EXISTS "location_objects" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "id" UUID NOT NULL PRIMARY KEY,
            "aliases" JSONB NOT NULL DEFAULT '[]'::jsonb,
            "club" VARCHAR(512),
            "club_id" UUID,
            "city" VARCHAR(255),
            "city_id" UUID,
            "region" VARCHAR(255) NOT NULL,
            "region_id" UUID NOT NULL,
            "required" JSONB NOT NULL DEFAULT '[]'::jsonb
        );

        CREATE TABLE IF NOT EXISTS "locations" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "id" SERIAL NOT NULL PRIMARY KEY,
            "alias" VARCHAR(512) NOT NULL,
            "athlete_id" INT NOT NULL
                REFERENCES "athletes" ("id") ON DELETE CASCADE,
            "location_object_id" UUID NOT NULL
                REFERENCES "location_objects" ("id") ON DELETE RESTRICT,
            CONSTRAINT "uid_locations_athlete_object_alias"
                UNIQUE ("athlete_id", "location_object_id", "alias")
        );

        CREATE INDEX IF NOT EXISTS "idx_location_objects_aliases"
            ON "location_objects" USING gin ("aliases");
        CREATE INDEX IF NOT EXISTS "idx_location_objects_club_trgm"
            ON "location_objects" USING gin ("club" gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS "idx_location_objects_city_trgm"
            ON "location_objects" USING gin ("city" gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS "idx_location_objects_region_trgm"
            ON "location_objects" USING gin ("region" gin_trgm_ops);
        CREATE INDEX IF NOT EXISTS "idx_location_objects_club_id"
            ON "location_objects" ("club_id");
        CREATE INDEX IF NOT EXISTS "idx_location_objects_city_id"
            ON "location_objects" ("city_id");
        CREATE INDEX IF NOT EXISTS "idx_location_objects_region_id"
            ON "location_objects" ("region_id");
        CREATE INDEX IF NOT EXISTS "idx_locations_athlete"
            ON "locations" ("athlete_id");
        CREATE INDEX IF NOT EXISTS "idx_locations_location_object"
            ON "locations" ("location_object_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "locations";
        DROP TABLE IF EXISTS "location_objects";
    """
