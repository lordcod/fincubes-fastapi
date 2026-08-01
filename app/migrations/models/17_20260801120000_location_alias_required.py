from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "location_aliases" (
            "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "id" UUID NOT NULL PRIMARY KEY,
            "location_object_id" UUID NOT NULL
                REFERENCES "location_objects" ("id") ON DELETE CASCADE,
            "alias" VARCHAR(512) NOT NULL,
            "alias_key" VARCHAR(512) NOT NULL,
            "required" JSONB NOT NULL DEFAULT '[]'::jsonb,
            CONSTRAINT "uid_location_alias_object_key"
                UNIQUE ("location_object_id", "alias_key")
        );

        INSERT INTO "location_aliases" (
            "created_at",
            "updated_at",
            "id",
            "location_object_id",
            "alias",
            "alias_key",
            "required"
        )
        SELECT
            location_object."created_at",
            location_object."updated_at",
            uuid_in(md5(location_object."id"::text || ':' || alias_item.value)::cstring),
            location_object."id",
            alias_item.value,
            lower(btrim(alias_item.value)),
            COALESCE(location_object."required", '[]'::jsonb)
        FROM "location_objects" AS location_object
        CROSS JOIN LATERAL jsonb_array_elements_text(
            COALESCE(location_object."aliases", '[]'::jsonb)
        ) AS alias_item(value)
        ON CONFLICT ("location_object_id", "alias_key") DO UPDATE
        SET
            "alias" = EXCLUDED."alias",
            "required" = EXCLUDED."required",
            "updated_at" = EXCLUDED."updated_at";

        CREATE INDEX IF NOT EXISTS "idx_location_aliases_alias_key"
            ON "location_aliases" ("alias_key");
        CREATE INDEX IF NOT EXISTS "idx_location_aliases_location_object"
            ON "location_aliases" ("location_object_id");

        DROP INDEX IF EXISTS "idx_location_objects_aliases";

        ALTER TABLE "location_objects"
            DROP COLUMN IF EXISTS "aliases",
            DROP COLUMN IF EXISTS "required";
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "location_objects"
            ADD COLUMN IF NOT EXISTS "aliases" JSONB NOT NULL DEFAULT '[]'::jsonb,
            ADD COLUMN IF NOT EXISTS "required" JSONB NOT NULL DEFAULT '[]'::jsonb;

        WITH alias_groups AS (
            SELECT
                "location_object_id",
                jsonb_agg("alias" ORDER BY "alias") AS aliases,
                COALESCE(
                    (
                        SELECT jsonb_agg(DISTINCT required_item.value)
                        FROM "location_aliases" AS required_alias
                        CROSS JOIN LATERAL jsonb_array_elements_text(
                            COALESCE(required_alias."required", '[]'::jsonb)
                        ) AS required_item(value)
                        WHERE required_alias."location_object_id" = location_alias."location_object_id"
                    ),
                    '[]'::jsonb
                ) AS required
            FROM "location_aliases" AS location_alias
            GROUP BY "location_object_id"
        )
        UPDATE "location_objects" AS location_object
        SET
            "aliases" = alias_groups.aliases,
            "required" = alias_groups.required
        FROM alias_groups
        WHERE location_object."id" = alias_groups."location_object_id";

        CREATE INDEX IF NOT EXISTS "idx_location_objects_aliases"
            ON "location_objects" USING gin ("aliases");

        DROP TABLE IF EXISTS "location_aliases";
    """
