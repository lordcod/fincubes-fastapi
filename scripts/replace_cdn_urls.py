"""Replace legacy CDN URLs in PostgreSQL text and JSON columns.

Usage:
    python scripts/replace_cdn_urls.py
    python scripts/replace_cdn_urls.py --apply
    python scripts/replace_cdn_urls.py --old-prefix https://cdn.fincubes.ru/ --new-prefix https://storage.yandexcloud.net/fincubes/
"""

import argparse
import asyncio
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from tortoise import Tortoise

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


DEFAULT_OLD_PREFIX = "https://cdn.fincubes.ru/"
DEFAULT_NEW_PREFIX = "https://storage.yandexcloud.net/fincubes/"

TEXT_TYPES = {
    "character varying",
    "character",
    "text",
}
JSON_TYPES = {
    "json",
    "jsonb",
}


@dataclass(frozen=True)
class TargetColumn:
    table_name: str
    column_name: str
    data_type: str

    @property
    def is_json(self) -> bool:
        return self.data_type in JSON_TYPES


def quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


async def list_target_columns() -> list[TargetColumn]:
    sql = """
        SELECT
            columns.table_name,
            columns.column_name,
            columns.data_type
        FROM information_schema.columns AS columns
        JOIN information_schema.tables AS tables
            ON tables.table_schema = columns.table_schema
            AND tables.table_name = columns.table_name
        WHERE columns.table_schema = 'public'
            AND tables.table_type = 'BASE TABLE'
            AND columns.data_type IN (
                'character varying',
                'character',
                'text',
                'json',
                'jsonb'
            )
        ORDER BY columns.table_name, columns.ordinal_position;
    """
    rows = await Tortoise.get_connection("default").execute_query_dict(sql)
    return [
        TargetColumn(
            table_name=row["table_name"],
            column_name=row["column_name"],
            data_type=row["data_type"],
        )
        for row in rows
    ]


async def count_matches(target: TargetColumn, old_prefix: str) -> int:
    table = quote_ident(target.table_name)
    column = quote_ident(target.column_name)
    old_like = quote_literal(f"%{old_prefix}%")
    sql = f"""
        SELECT count(*) AS count
        FROM {table}
        WHERE {column} IS NOT NULL
            AND {column}::text LIKE {old_like};
    """
    rows = await Tortoise.get_connection("default").execute_query_dict(sql)
    return int(rows[0]["count"])


async def update_column(target: TargetColumn, old_prefix: str, new_prefix: str) -> None:
    table = quote_ident(target.table_name)
    column = quote_ident(target.column_name)
    old_literal = quote_literal(old_prefix)
    new_literal = quote_literal(new_prefix)
    old_like = quote_literal(f"%{old_prefix}%")

    if target.data_type in TEXT_TYPES:
        expression = f"replace({column}, {old_literal}, {new_literal})"
    elif target.data_type == "json":
        expression = f"replace({column}::text, {old_literal}, {new_literal})::json"
    elif target.data_type == "jsonb":
        expression = f"replace({column}::text, {old_literal}, {new_literal})::jsonb"
    else:
        raise ValueError(f"Unsupported column type: {target.data_type}")

    sql = f"""
        UPDATE {table}
        SET {column} = {expression}
        WHERE {column} IS NOT NULL
            AND {column}::text LIKE {old_like};
    """
    await Tortoise.get_connection("default").execute_script(sql)


async def run(args: argparse.Namespace) -> int:
    db_url = args.database_url or os.environ.get("DATABASE_URL")
    if db_url:
        await Tortoise.init(db_url=db_url, modules={"models": ["app.models"]})
    else:
        from app.core.config.tortoise_orm import TORTOISE_ORM

        await Tortoise.init(config=TORTOISE_ORM)

    try:
        targets = await list_target_columns()
        matches: list[tuple[TargetColumn, int]] = []
        for target in targets:
            count = await count_matches(target, args.old_prefix)
            if count:
                matches.append((target, count))

        if not matches:
            print("No legacy CDN URLs found.")
            return 0

        print("Legacy CDN URL matches:")
        for target, count in matches:
            print(
                f"  {target.table_name}.{target.column_name} "
                f"({target.data_type}): {count}"
            )
        print(f"Total affected rows across columns: {sum(count for _, count in matches)}")

        if not args.apply:
            print("Dry-run only. Re-run with --apply to update the database.")
            return 0

        for target, _ in matches:
            await update_column(target, args.old_prefix, args.new_prefix)

        remaining = 0
        for target, _ in matches:
            remaining += await count_matches(target, args.old_prefix)

        print(f"Replacement applied. Remaining legacy matches: {remaining}")
        return 0 if remaining == 0 else 1
    finally:
        await Tortoise.close_connections()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replace legacy CDN URLs in all PostgreSQL text/json columns.",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--database-url",
        help="Tortoise database URL. Defaults to DATABASE_URL or app settings.",
    )
    parser.add_argument("--old-prefix", default=DEFAULT_OLD_PREFIX)
    parser.add_argument("--new-prefix", default=DEFAULT_NEW_PREFIX)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(run(parse_args())))
