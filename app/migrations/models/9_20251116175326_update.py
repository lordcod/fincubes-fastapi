from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "results" ADD "metadata" JSONB DEFAULT '{}';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "results" DROP COLUMN "metadata";"""
