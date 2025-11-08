from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "competitions" ADD "course" VARCHAR(10);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "competitions" DROP COLUMN "course";"""
