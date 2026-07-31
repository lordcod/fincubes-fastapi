from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "athletes"
            ADD COLUMN IF NOT EXISTS "location_object_id" UUID
                REFERENCES "location_objects" ("id") ON DELETE SET NULL;

        DO $$
        BEGIN
            IF to_regclass('public.locations') IS NOT NULL THEN
                UPDATE "athletes" AS athlete
                SET "location_object_id" = location_link."location_object_id"
                FROM (
                    SELECT DISTINCT ON ("athlete_id")
                        "athlete_id",
                        "location_object_id"
                    FROM "locations"
                    ORDER BY "athlete_id", "updated_at" DESC, "id" DESC
                ) AS location_link
                WHERE athlete."location_object_id" IS NULL
                    AND athlete."id" = location_link."athlete_id";
            END IF;
        END $$;

        WITH candidates AS (
            SELECT
                athlete."id" AS athlete_id,
                location_object."id" AS location_object_id,
                CASE
                    WHEN NULLIF(TRIM(COALESCE(athlete."club", '')), '') IS NOT NULL
                        AND NULLIF(TRIM(COALESCE(athlete."city", '')), '') IS NOT NULL
                        AND NULLIF(TRIM(COALESCE(athlete."region", '')), '') IS NOT NULL
                        AND lower(TRIM(athlete."club")) = lower(TRIM(COALESCE(location_object."club", '')))
                        AND lower(TRIM(athlete."city")) = lower(TRIM(COALESCE(location_object."city", '')))
                        AND lower(TRIM(athlete."region")) = lower(TRIM(location_object."region"))
                        THEN 10
                    WHEN NULLIF(TRIM(COALESCE(athlete."club", '')), '') IS NOT NULL
                        AND NULLIF(TRIM(COALESCE(athlete."city", '')), '') IS NOT NULL
                        AND lower(TRIM(athlete."club")) = lower(TRIM(COALESCE(location_object."club", '')))
                        AND lower(TRIM(athlete."city")) = lower(TRIM(COALESCE(location_object."city", '')))
                        THEN 20
                    WHEN NULLIF(TRIM(COALESCE(athlete."club", '')), '') IS NOT NULL
                        AND lower(TRIM(athlete."club")) = lower(TRIM(COALESCE(location_object."club", '')))
                        THEN 30
                    WHEN NULLIF(TRIM(COALESCE(athlete."club", '')), '') IS NULL
                        AND NULLIF(TRIM(COALESCE(athlete."city", '')), '') IS NOT NULL
                        AND NULLIF(TRIM(COALESCE(athlete."region", '')), '') IS NOT NULL
                        AND lower(TRIM(athlete."city")) = lower(TRIM(COALESCE(location_object."city", '')))
                        AND lower(TRIM(athlete."region")) = lower(TRIM(location_object."region"))
                        THEN 40
                    WHEN NULLIF(TRIM(COALESCE(athlete."club", '')), '') IS NULL
                        AND NULLIF(TRIM(COALESCE(athlete."city", '')), '') IS NOT NULL
                        AND lower(TRIM(athlete."city")) = lower(TRIM(COALESCE(location_object."city", '')))
                        THEN 50
                    ELSE NULL
                END AS priority
            FROM "athletes" AS athlete
            CROSS JOIN "location_objects" AS location_object
            WHERE athlete."location_object_id" IS NULL
        ),
        ranked AS (
            SELECT
                athlete_id,
                location_object_id,
                priority,
                COUNT(*) OVER (
                    PARTITION BY athlete_id, priority
                ) AS priority_matches,
                ROW_NUMBER() OVER (
                    PARTITION BY athlete_id
                    ORDER BY priority, location_object_id
                ) AS row_number
            FROM candidates
            WHERE priority IS NOT NULL
        ),
        best AS (
            SELECT athlete_id, location_object_id
            FROM ranked
            WHERE row_number = 1
                AND priority_matches = 1
        )
        UPDATE "athletes" AS athlete
        SET "location_object_id" = best."location_object_id"
        FROM best
        WHERE athlete."id" = best."athlete_id";

        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM "athletes"
                WHERE "location_object_id" IS NULL
                    AND (
                        NULLIF(TRIM(COALESCE("club", '')), '') IS NOT NULL
                        OR NULLIF(TRIM(COALESCE("city", '')), '') IS NOT NULL
                        OR NULLIF(TRIM(COALESCE("region", '')), '') IS NOT NULL
                    )
            ) THEN
                RAISE EXCEPTION 'athlete location migration stopped: some athletes still have club/city/region values without unambiguous location_object_id';
            END IF;
        END $$;

        CREATE INDEX IF NOT EXISTS "idx_athletes_location_object"
            ON "athletes" ("location_object_id");

        ALTER TABLE "athletes"
            DROP COLUMN IF EXISTS "club",
            DROP COLUMN IF EXISTS "city",
            DROP COLUMN IF EXISTS "region";

        DROP TABLE IF EXISTS "locations";
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
