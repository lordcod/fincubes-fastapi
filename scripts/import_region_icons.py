import argparse
import asyncio
import csv
import hashlib
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from tortoise import Tortoise

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.integrations.yandexcloud import make_cloud_url
from app.models.misc.region_icon import RegionIcon


TRANSLIT = {
    "\u0430": "a",
    "\u0431": "b",
    "\u0432": "v",
    "\u0433": "g",
    "\u0434": "d",
    "\u0435": "e",
    "\u0451": "e",
    "\u0436": "zh",
    "\u0437": "z",
    "\u0438": "i",
    "\u0439": "y",
    "\u043a": "k",
    "\u043b": "l",
    "\u043c": "m",
    "\u043d": "n",
    "\u043e": "o",
    "\u043f": "p",
    "\u0440": "r",
    "\u0441": "s",
    "\u0442": "t",
    "\u0443": "u",
    "\u0444": "f",
    "\u0445": "kh",
    "\u0446": "ts",
    "\u0447": "ch",
    "\u0448": "sh",
    "\u0449": "shch",
    "\u044a": "",
    "\u044b": "y",
    "\u044c": "",
    "\u044d": "e",
    "\u044e": "yu",
    "\u044f": "ya",
}

@dataclass
class ImportSummary:
    rows: int = 0
    uploaded_files: int = 0
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    skipped_missing_files: int = 0
    skipped_empty_rows: int = 0


def slugify(value: str) -> str:
    value = "".join(TRANSLIT.get(ch, ch) for ch in value.casefold())
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "region"


def detect_format(path: Path) -> str:
    return path.suffix.lower().lstrip(".") or "unknown"


def object_path_for(source_path: Path) -> str:
    digest = hashlib.sha256(source_path.read_bytes()).hexdigest()[:12]
    stem = slugify(source_path.stem)
    ext = source_path.suffix.lower()
    return f"region-coats/{stem}-{digest}{ext}"


def resolve_asset_path(csv_path: Path, asset_path: str) -> Path:
    candidate = Path(asset_path)
    if candidate.is_absolute():
        return candidate

    for base_path in (csv_path.parent, *csv_path.parent.parents):
        resolved = (base_path / candidate).resolve()
        if resolved.exists():
            return resolved
        if "*" in asset_path:
            matches = sorted(base_path.glob(asset_path))
            if matches:
                return matches[0].resolve()

    return (csv_path.parent / candidate).resolve()


async def upload_with_retries(
    body: bytes,
    object_path: str,
    *,
    attempts: int = 4,
) -> str:
    from app.integrations.yandexcloud import upload_file

    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await upload_file(body, object_path)
        except Exception as exc:
            last_exc = exc
            if attempt == attempts:
                break
            delay = min(2 ** (attempt - 1), 8)
            print(f"WARN upload failed, retry {attempt}/{attempts}: {object_path} -> {exc}")
            await asyncio.sleep(delay)

    raise RuntimeError(f"Upload failed after {attempts} attempts: {object_path}") from last_exc


async def import_region_icons(
    csv_path: Path,
    *,
    apply: bool,
    upload: bool,
    progress: bool,
) -> ImportSummary:
    summary = ImportSummary()
    uploaded_urls_by_source: dict[Path, str] = {}

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file))

    if not rows:
        return summary

    data_rows = rows[1:]
    total = len(data_rows)

    for index, row in enumerate(data_rows, start=1):
        summary.rows += 1
        if progress and (index == total or index % 25 == 0):
            print(f"region icons: {index}/{total}")

        name = row[0].strip() if len(row) > 0 else ""
        source = row[1].strip() if len(row) > 1 else ""
        if not name or not source:
            summary.skipped_empty_rows += 1
            continue

        asset_path = resolve_asset_path(csv_path, source)
        if not asset_path.exists():
            summary.skipped_missing_files += 1
            print(f"SKIP missing file: {name} -> {asset_path}")
            continue

        file_format = detect_format(asset_path)
        object_path = object_path_for(asset_path)
        icon_url = make_cloud_url(object_path)
        existing = await RegionIcon.get_or_none(name=name)

        if (
            apply
            and existing is not None
            and existing.format == file_format
            and existing.icon_url == icon_url
        ):
            summary.unchanged += 1
            continue

        if apply and upload:
            if asset_path in uploaded_urls_by_source:
                icon_url = uploaded_urls_by_source[asset_path]
            else:
                icon_url = await upload_with_retries(asset_path.read_bytes(), object_path)
                uploaded_urls_by_source[asset_path] = icon_url
                summary.uploaded_files += 1

        if not apply:
            if existing is None:
                summary.created += 1
            else:
                summary.updated += 1
            continue

        if existing is None:
            await RegionIcon.create(
                name=name,
                format=file_format,
                icon_url=icon_url,
            )
            summary.created += 1
        else:
            existing.format = file_format
            existing.icon_url = icon_url
            await existing.save(update_fields=["format", "icon_url", "updated_at"])
            summary.updated += 1

    return summary


async def check_cloud_upload() -> None:
    from app.integrations.yandexcloud import CloudError, upload_file

    object_path = f"region-coats/.upload-check-{int(time.time())}.txt"
    try:
        await upload_file(b"ok", object_path)
    except CloudError as exc:
        raise RuntimeError(
            "S3 upload preflight failed. Проверь Doppler secrets "
            "AWS_KEY_ID/AWS_SECRET_KEY: Yandex Object Storage отверг ключ. "
            f"Original error: {exc}"
        ) from exc


async def run(args: argparse.Namespace) -> None:
    from app.core.config.tortoise_orm import TORTOISE_ORM

    should_open_http_session = args.apply and not args.no_upload
    if should_open_http_session:
        import aiohttp

        from app.shared.clients import session

        session.session = aiohttp.ClientSession()
    else:
        session = None

    await Tortoise.init(config=TORTOISE_ORM)
    try:
        if should_open_http_session:
            await check_cloud_upload()

        summary = await import_region_icons(
            args.csv_path.resolve(),
            apply=args.apply,
            upload=not args.no_upload,
            progress=args.progress,
        )
    finally:
        await Tortoise.close_connections()
        if should_open_http_session and session.session is not None:
            await session.session.close()
            session.session = None

    mode = "apply" if args.apply else "dry-run"
    print(
        f"{mode}: rows={summary.rows} created={summary.created} "
        f"updated={summary.updated} unchanged={summary.unchanged} "
        f"uploaded_files={summary.uploaded_files} "
        f"skipped_missing_files={summary.skipped_missing_files} "
        f"skipped_empty_rows={summary.skipped_empty_rows}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "csv_path",
        type=Path,
        help="Path to region-coats-local.csv",
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Do not upload files, only write deterministic Object Storage URLs.",
    )
    parser.add_argument("--progress", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
