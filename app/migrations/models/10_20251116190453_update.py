from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "results" ALTER COLUMN "metadata" DROP DEFAULT;
        ALTER TABLE "results" ALTER COLUMN "metadata" DROP NOT NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "results" ALTER COLUMN "metadata" SET NOT NULL;
        ALTER TABLE "results" ALTER COLUMN "metadata" SET;"""
