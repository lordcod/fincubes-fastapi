from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "review_session" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "status" VARCHAR(20) NOT NULL DEFAULT 'new',
    "source_type" VARCHAR(64) NOT NULL,
    "source_ref" VARCHAR(255) NOT NULL,
    "meta" JSONB NOT NULL DEFAULT '{}'::jsonb,
    "created_by_id" INT REFERENCES "user" ("id") ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS "review_item" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "external_id" VARCHAR(255) NOT NULL,
    "status" VARCHAR(32) NOT NULL DEFAULT 'new',
    "source_payload" JSONB NOT NULL,
    "source_city" VARCHAR(255),
    "candidates_snapshot" JSONB NOT NULL DEFAULT '[]'::jsonb,
    "candidate_count" INT NOT NULL DEFAULT 0,
    "auto_match" BOOL NOT NULL DEFAULT FALSE,
    "confidence" VARCHAR(16) NOT NULL DEFAULT 'low',
    "note" TEXT,
    "selected_athlete_id" INT REFERENCES "athletes" ("id") ON DELETE SET NULL,
    "session_id" INT NOT NULL REFERENCES "review_session" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_review_item_session_external" UNIQUE ("session_id", "external_id")
);
CREATE TABLE IF NOT EXISTS "review_decision" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "action" VARCHAR(32) NOT NULL,
    "patch_payload" JSONB,
    "result_payload" JSONB,
    "candidate_athlete_id" INT REFERENCES "athletes" ("id") ON DELETE SET NULL,
    "created_athlete_id" INT REFERENCES "athletes" ("id") ON DELETE SET NULL,
    "created_by_id" INT REFERENCES "user" ("id") ON DELETE SET NULL,
    "review_item_id" INT NOT NULL REFERENCES "review_item" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_review_session_status" ON "review_session" ("status");
CREATE INDEX IF NOT EXISTS "idx_review_item_session_status" ON "review_item" ("session_id", "status");
CREATE INDEX IF NOT EXISTS "idx_review_item_session_auto_match" ON "review_item" ("session_id", "auto_match");
CREATE INDEX IF NOT EXISTS "idx_review_item_session_city" ON "review_item" ("session_id", "source_city");
CREATE INDEX IF NOT EXISTS "idx_review_item_session_candidate_count" ON "review_item" ("session_id", "candidate_count");
CREATE INDEX IF NOT EXISTS "idx_review_decision_review_item" ON "review_decision" ("review_item_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "review_decision";
DROP TABLE IF EXISTS "review_item";
DROP TABLE IF EXISTS "review_session";"""
