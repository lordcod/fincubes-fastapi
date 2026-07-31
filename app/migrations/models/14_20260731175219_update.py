from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "athletes" ADD "location_object_id" UUID;
        ALTER TABLE "athletes" DROP COLUMN "city";
        ALTER TABLE "athletes" DROP COLUMN "club";
        ALTER TABLE "location_objects" DROP COLUMN "region_id";
        ALTER TABLE "location_objects" DROP COLUMN "club_id";
        ALTER TABLE "location_objects" DROP COLUMN "city_id";
        DROP TABLE IF EXISTS "locations";
        ALTER TABLE "athletes" ADD CONSTRAINT "fk_athletes_location_725e26e7" FOREIGN KEY ("location_object_id") REFERENCES "location_objects" ("id") ON DELETE SET NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "athletes" DROP CONSTRAINT IF EXISTS "fk_athletes_location_725e26e7";
        ALTER TABLE "athletes" ADD "city" VARCHAR(255);
        ALTER TABLE "athletes" ADD "club" VARCHAR(255);
        ALTER TABLE "athletes" DROP COLUMN "location_object_id";
        ALTER TABLE "location_objects" ADD "region_id" UUID NOT NULL;
        ALTER TABLE "location_objects" ADD "club_id" UUID;
        ALTER TABLE "location_objects" ADD "city_id" UUID;"""
