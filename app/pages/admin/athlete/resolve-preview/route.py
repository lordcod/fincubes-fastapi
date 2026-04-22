from fastapi import APIRouter, Depends

from app.core.errors import APIError, ErrorCode
from app.models.athlete.athlete import Athlete
from app.schemas.athlete.review import (
    BulkAthleteCreateItem,
    ResolvePreviewCreateItem,
    ResolvePreviewEnrichItem,
    ResolvePreviewRequest,
    ResolvePreviewResponse,
    ResolvePreviewSummary,
)
from app.shared.utils.athlete_identity import build_suggested_patch
from app.shared.utils.scopes.request import require_scope

router = APIRouter()


@router.post(
    "/",
    response_model=ResolvePreviewResponse,
)
@require_scope("athlete:read")
async def resolve_preview(payload: ResolvePreviewRequest):
    summary = ResolvePreviewSummary()
    enrich_updates: list[ResolvePreviewEnrichItem] = []
    create_payloads: list[ResolvePreviewCreateItem] = []

    athlete_ids = [item.athlete_id for item in payload.items if item.athlete_id is not None]
    athletes = await Athlete.filter(id__in=athlete_ids).all() if athlete_ids else []
    athletes_by_id = {athlete.id: athlete for athlete in athletes}

    for item in payload.items:
        if item.action == "match":
            if item.athlete_id is None:
                raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

            athlete = athletes_by_id.get(item.athlete_id)
            if athlete is None:
                raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

            summary.matched += 1

            if item.source is not None:
                patch = build_suggested_patch(item.source, athlete)
                if patch is not None:
                    enrich_updates.append(
                        ResolvePreviewEnrichItem(
                            external_id=item.external_id,
                            athlete_id=athlete.id,
                            suggested_patch=patch,
                        )
                    )
                    summary.enrich_updates += 1

        elif item.action == "create_new":
            summary.create_new += 1
            if item.source is not None:
                create_payloads.append(
                    ResolvePreviewCreateItem(
                        external_id=item.external_id,
                        payload=BulkAthleteCreateItem(
                            external_id=item.external_id,
                            last_name=item.source.last_name,
                            first_name=item.source.first_name,
                            birth_year=item.source.birth_year,
                            gender=(item.source.gender or "").upper(),
                            city=item.source.city,
                            club=item.source.team,
                            license=item.source.rank,
                        ),
                    )
                )
        elif item.action == "skip":
            summary.skipped += 1
        else:
            summary.need_manual += 1

    return ResolvePreviewResponse(
        summary=summary,
        enrich_updates=enrich_updates,
        create_payloads=create_payloads,
    )
