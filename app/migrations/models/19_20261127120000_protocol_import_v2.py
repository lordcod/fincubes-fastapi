from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return '''
        ALTER TABLE "athletes"
            ADD COLUMN IF NOT EXISTS "club" VARCHAR(512),
            ADD COLUMN IF NOT EXISTS "city" VARCHAR(255),
            ADD COLUMN IF NOT EXISTS "region" VARCHAR(255);
        ALTER TABLE "athletes" ALTER COLUMN "club" TYPE VARCHAR(512);
        UPDATE "athletes" AS a
        SET "club" = l."club", "city" = l."city", "region" = l."region"
        FROM "location_objects" AS l WHERE a."location_object_id" = l."id";
        ALTER TABLE "protocol_imports" ALTER COLUMN "competition_id" DROP NOT NULL;
    '''


async def downgrade(db: BaseDBAsyncClient) -> str:
    # Keep affiliation text: dictionary edits cannot reconstruct these snapshots.
    return '''
        DELETE FROM "protocol_imports" WHERE "competition_id" IS NULL;
        ALTER TABLE "protocol_imports" ALTER COLUMN "competition_id" SET NOT NULL;
    '''
