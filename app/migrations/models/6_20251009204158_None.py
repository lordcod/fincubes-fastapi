from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "athletes" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "last_name" VARCHAR(100) NOT NULL,
    "first_name" VARCHAR(100) NOT NULL,
    "birth_year" VARCHAR(4) NOT NULL,
    "club" VARCHAR(255),
    "city" VARCHAR(255),
    "license" VARCHAR(50),
    "gender" VARCHAR(1) NOT NULL,
    "avatar_url" VARCHAR(250),
    "is_top" BOOL NOT NULL DEFAULT False
);
CREATE TABLE IF NOT EXISTS "coach" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "last_name" VARCHAR(100) NOT NULL,
    "first_name" VARCHAR(100) NOT NULL,
    "middle_name" VARCHAR(100) NOT NULL,
    "club" VARCHAR(255) NOT NULL,
    "city" VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS "coachathlete" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "status" VARCHAR(50) NOT NULL DEFAULT 'active',
    "athlete_id" INT NOT NULL REFERENCES "athletes" ("id") ON DELETE CASCADE,
    "coach_id" INT NOT NULL REFERENCES "coach" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "competitions" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL,
    "date" VARCHAR(50) NOT NULL,
    "location" VARCHAR(255) NOT NULL,
    "city" VARCHAR(255),
    "organizer" VARCHAR(100) NOT NULL,
    "status" VARCHAR(100),
    "links" JSONB NOT NULL,
    "start_date" DATE NOT NULL,
    "end_date" DATE NOT NULL,
    "last_processed_at" TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS "distances" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "order" INT NOT NULL,
    "stroke" VARCHAR(50) NOT NULL,
    "distance" INT NOT NULL,
    "category" VARCHAR(255),
    "gender" VARCHAR(1) NOT NULL,
    "min_year" INT,
    "max_year" INT,
    "competition_id" INT NOT NULL REFERENCES "competitions" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "parents" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS "recent_events" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "competition_id" INT NOT NULL REFERENCES "competitions" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "records" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "stroke" VARCHAR(50) NOT NULL,
    "distance" INT NOT NULL,
    "time" VARCHAR(20) NOT NULL,
    "firstname" VARCHAR(100) NOT NULL,
    "lastname" VARCHAR(100) NOT NULL,
    "birth_year" INT NOT NULL,
    "region" VARCHAR(100) NOT NULL,
    "date" DATE NOT NULL,
    "city" VARCHAR(100) NOT NULL,
    "country" VARCHAR(100),
    "event_name" VARCHAR(100) NOT NULL,
    "gender" VARCHAR(1),
    "category" VARCHAR(5),
    "is_active" BOOL NOT NULL DEFAULT True
);
CREATE TABLE IF NOT EXISTS "region" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "region" VARCHAR(255) NOT NULL,
    "organization" VARCHAR(512) NOT NULL,
    "president" VARCHAR(255) NOT NULL,
    "emails" JSONB NOT NULL,
    "phones" JSONB NOT NULL,
    "socials" JSONB NOT NULL,
    "rating" DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS "results" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "stroke" VARCHAR(50) NOT NULL,
    "distance" INT NOT NULL,
    "result" TIMETZ,
    "final" TIMETZ,
    "resolved_time" TIMETZ,
    "place" VARCHAR(50),
    "final_rank" VARCHAR(50),
    "points" VARCHAR(50),
    "record" VARCHAR(255),
    "status" VARCHAR(20) NOT NULL DEFAULT 'COMPLETED',
    "athlete_id" INT NOT NULL REFERENCES "athletes" ("id") ON DELETE CASCADE,
    "competition_id" INT NOT NULL REFERENCES "competitions" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "sessions" (
    "id" UUID NOT NULL PRIMARY KEY,
    "user_id" INT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "revoked_at" TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS "refresh_tokens" (
    "id" UUID NOT NULL PRIMARY KEY,
    "access_id" UUID,
    "issued_at" TIMESTAMPTZ NOT NULL,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "revoked_at" TIMESTAMPTZ,
    "grace_until" TIMESTAMPTZ,
    "request_info" JSONB,
    "session_id" UUID NOT NULL REFERENCES "sessions" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "standardcategory" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "code" VARCHAR(10) NOT NULL,
    "stroke" VARCHAR(10) NOT NULL,
    "distance" INT NOT NULL,
    "gender" VARCHAR(1) NOT NULL,
    "type" VARCHAR(10) NOT NULL,
    "result" TIMETZ,
    "is_active" BOOL NOT NULL DEFAULT True
);
CREATE TABLE IF NOT EXISTS "top_athletes" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "athlete_id" INT NOT NULL REFERENCES "athletes" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "user" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "email" VARCHAR(255) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "verified" BOOL NOT NULL DEFAULT False,
    "scopes" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "bot" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "scopes" JSONB NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "owner_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "userrole" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "role_type" VARCHAR(9) NOT NULL,
    "profile_id" INT NOT NULL,
    "user_id" INT NOT NULL UNIQUE REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "userrole"."role_type" IS 'ATHLETE: ATHLETE\nCOACH: COACH\nPARENT: PARENT\nADMIN: ADMIN\nORGANIZER: ORGANIZER';
CREATE TABLE IF NOT EXISTS "userverification" (
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "id" SERIAL NOT NULL PRIMARY KEY,
    "attempt" INT NOT NULL DEFAULT 0,
    "is_active" BOOL NOT NULL DEFAULT True,
    "token" VARCHAR(256) NOT NULL,
    "token_expiry" TIMESTAMPTZ NOT NULL,
    "token_type" VARCHAR(14) NOT NULL DEFAULT 'VERIFY_EMAIL',
    "state" VARCHAR(1024) NOT NULL,
    "user_id" INT NOT NULL REFERENCES "user" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "userverification"."token_type" IS 'RESET_PASSWORD: RESET_PASSWORD\nVERIFY_EMAIL: VERIFY_EMAIL';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "parents_athletes" (
    "parents_id" INT NOT NULL REFERENCES "parents" ("id") ON DELETE CASCADE,
    "athlete_id" INT NOT NULL REFERENCES "athletes" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_parents_ath_parents_75aabf" ON "parents_athletes" ("parents_id", "athlete_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
