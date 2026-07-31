from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "athletes"
            ADD COLUMN IF NOT EXISTS "region" VARCHAR(255);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "athletes"
            DROP COLUMN IF EXISTS "region";"""
