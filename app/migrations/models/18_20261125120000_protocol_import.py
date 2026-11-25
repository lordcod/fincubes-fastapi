from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE "protocol_imports" (
            "id" UUID PRIMARY KEY,
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "competition_id" INT NOT NULL REFERENCES "competitions" ("id") ON DELETE CASCADE,
            "stage" VARCHAR(20) NOT NULL DEFAULT 'prepare',
            "payload" JSONB NOT NULL,
            "state" JSONB NOT NULL
        );
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return 'DROP TABLE "protocol_imports";'
