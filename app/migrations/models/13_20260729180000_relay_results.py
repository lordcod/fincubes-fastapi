from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "distances"
            ADD COLUMN IF NOT EXISTS "relay_count" INT NOT NULL DEFAULT 1;

        ALTER TABLE "distances"
            ADD CONSTRAINT "ck_distances_relay_count_positive"
            CHECK ("relay_count" > 0);

        CREATE TABLE IF NOT EXISTS "relay_results" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "id" SERIAL NOT NULL PRIMARY KEY,
            "name" VARCHAR(512) NOT NULL,
            "stroke" VARCHAR(50) NOT NULL,
            "distance" INT NOT NULL,
            "relay_count" INT NOT NULL DEFAULT 1,
            "gender" VARCHAR(1) NOT NULL,
            "result" TIMETZ,
            "place" VARCHAR(50),
            "points" VARCHAR(50),
            "status" VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
            "metadata" JSONB,
            "competition_id" INT NOT NULL
                REFERENCES "competitions" ("id") ON DELETE CASCADE,
            CONSTRAINT "ck_relay_results_distance_positive"
                CHECK ("distance" > 0),
            CONSTRAINT "ck_relay_results_relay_count"
                CHECK ("relay_count" > 1)
        );

        CREATE TABLE IF NOT EXISTS "relay_legs" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "id" SERIAL NOT NULL PRIMARY KEY,
            "order" INT NOT NULL,
            "result" TIMETZ,
            "metadata" JSONB,
            "athlete_id" INT NOT NULL
                REFERENCES "athletes" ("id") ON DELETE RESTRICT,
            "relay_result_id" INT NOT NULL
                REFERENCES "relay_results" ("id") ON DELETE CASCADE,
            CONSTRAINT "ck_relay_legs_order_positive"
                CHECK ("order" > 0),
            CONSTRAINT "uid_relay_legs_result_order"
                UNIQUE ("relay_result_id", "order")
        );

        CREATE INDEX IF NOT EXISTS "idx_relay_results_competition"
            ON "relay_results" ("competition_id");
        CREATE INDEX IF NOT EXISTS "idx_relay_results_event"
            ON "relay_results"
            ("competition_id", "stroke", "distance", "relay_count", "gender");
        CREATE INDEX IF NOT EXISTS "idx_relay_legs_athlete"
            ON "relay_legs" ("athlete_id");
        CREATE INDEX IF NOT EXISTS "idx_relay_legs_result"
            ON "relay_legs" ("relay_result_id");
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "relay_legs";
        DROP TABLE IF EXISTS "relay_results";

        ALTER TABLE "distances"
            DROP CONSTRAINT IF EXISTS "ck_distances_relay_count_positive";
        ALTER TABLE "distances"
            DROP COLUMN IF EXISTS "relay_count";
    """
