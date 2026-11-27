"""Editable alias dictionary; edits never rewrite athlete affiliation snapshots."""
from uuid import UUID
from fastapi import APIRouter
from pydantic import Field, field_validator
from tortoise.transactions import in_transaction

from app.core.errors import APIError, ErrorCode
from app.models.location.location_object import LocationObject
from app.models.location.location_alias import LocationAlias
from app.schemas.admin.protocol_import import TeamFields
from app.shared.utils.location_text import normalize_location_text
from app.shared.utils.scopes.request import require_scope

router = APIRouter(tags=["Admin/Team dictionary"])


class DictionaryEntry(TeamFields):
    aliases: list[str] = Field(min_length=1)
    required: list[str] = Field(default_factory=list)

    @field_validator("aliases")
    @classmethod
    def aliases_valid(cls, values):
        cleaned = [v.strip() for v in values]
        if any(not v or len(v) > 512 for v in cleaned):
            raise ValueError("Aliases must contain 1–512 characters")
        if len({normalize_location_text(v) for v in cleaned}) != len(cleaned):
            raise ValueError("Aliases must be unique")
        return cleaned

    @field_validator("required")
    @classmethod
    def context_valid(cls, values):
        if set(values) - {"city", "region"}:
            raise ValueError("Only city and region may be required")
        return sorted(set(values))


@router.get("/")
@require_scope("athlete:read")
async def dictionary(query: str = ""):
    rows = await LocationObject.all().prefetch_related("alias_rules")
    output = []
    for row in rows:
        aliases = [{"alias": a.alias, "required": a.required} for a in row.alias_rules]
        if not aliases:
            continue
        if query and not any(normalize_location_text(query) in normalize_location_text(value or "")
                             for value in [row.club, row.city, row.region, *[a["alias"] for a in aliases]]):
            continue
        output.append({"id": str(row.id), "club": row.club, "city": row.city, "region": row.region or None, "aliases": aliases})
    return output


async def save_entry(payload, entry_id=None):
    async with in_transaction() as db:
        if entry_id:
            row = await LocationObject.filter(id=entry_id).using_db(db).select_for_update().first()
            if row is None:
                raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)
            row.update_from_dict({"club": payload.club, "city": payload.city, "region": payload.region or ""})
            await row.save(using_db=db)
            await LocationAlias.filter(location_object_id=row.id).using_db(db).delete()
        else:
            row = await LocationObject.create(club=payload.club, city=payload.city, region=payload.region or "", using_db=db)
        for alias in payload.aliases:
            await LocationAlias.create(location_object_id=row.id, alias=alias,
                                       alias_key=normalize_location_text(alias), required=payload.required, using_db=db)
        return {"id": str(row.id), **payload.model_dump()}


@router.post("/")
@require_scope("athlete:create")
async def create_entry(payload: DictionaryEntry):
    return await save_entry(payload)


@router.put("/{entry_id}/")
@require_scope("athlete:write")
async def edit_entry(entry_id: UUID, payload: DictionaryEntry):
    return await save_entry(payload, entry_id)


@router.delete("/{entry_id}/")
@require_scope("athlete:write")
async def delete_entry(entry_id: UUID):
    # Keep historical dictionary objects and remove only active resolution rules.
    if not await LocationObject.filter(id=entry_id).exists():
        raise APIError(ErrorCode.LOCATION_OBJECT_NOT_FOUND)
    await LocationAlias.filter(location_object_id=entry_id).delete()
    return {"id": str(entry_id), "aliases_removed": True}
