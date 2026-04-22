from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.athlete.athlete import Athlete_Pydantic
from app.shared.enums.enums import (
    ReviewConfidenceEnum,
    ReviewDecisionActionEnum,
    ReviewItemStatusEnum,
    ReviewSessionStatusEnum,
    ReviewSourceTypeEnum,
)


class ResolveCandidateSourceItem(BaseModel):
    external_id: str
    last_name: str
    first_name: str
    birth_year: int
    gender: Optional[str] = None
    city: Optional[str] = None
    team: Optional[str] = None
    rank: Optional[str] = None


class ResolveCandidatesRequest(BaseModel):
    items: list[ResolveCandidateSourceItem] = Field(default_factory=list)


class SuggestedPatch(BaseModel):
    club: Optional[str] = None
    city: Optional[str] = None
    license: Optional[str] = None


class ResolveCandidateItem(BaseModel):
    id: int
    last_name: str
    first_name: str
    birth_year: int
    gender: str
    city: Optional[str] = None
    club: Optional[str] = None
    license: Optional[str] = None
    score: int
    confidence: ReviewConfidenceEnum
    reasons: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    suggested_patch: Optional[SuggestedPatch] = None


class ResolveCandidatesResponseItem(BaseModel):
    external_id: str
    candidates: list[ResolveCandidateItem] = Field(default_factory=list)
    auto_match: bool = False
    confidence: ReviewConfidenceEnum = ReviewConfidenceEnum.LOW


class ResolveCandidatesResponse(BaseModel):
    items: list[ResolveCandidatesResponseItem] = Field(default_factory=list)


class BulkAthleteUpdateItem(BaseModel):
    id: int
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    birth_year: Optional[int] = None
    gender: Optional[str] = None
    city: Optional[str] = None
    club: Optional[str] = None
    license: Optional[str] = None


class BulkAthleteUpdateRequest(BaseModel):
    items: list[BulkAthleteUpdateItem] = Field(default_factory=list)


class BulkAthleteUpdateResponse(BaseModel):
    items: list[Athlete_Pydantic] = Field(default_factory=list)


class BulkAthleteCreateItem(BaseModel):
    external_id: Optional[str] = None
    last_name: str
    first_name: str
    birth_year: int
    gender: str
    city: Optional[str] = None
    club: Optional[str] = None
    license: Optional[str] = None


class BulkAthleteCreateRequest(BaseModel):
    items: list[BulkAthleteCreateItem] = Field(default_factory=list)


class BulkAthleteCreateResultItem(BaseModel):
    external_id: Optional[str] = None
    athlete: Athlete_Pydantic


class BulkAthleteCreateResponse(BaseModel):
    items: list[BulkAthleteCreateResultItem] = Field(default_factory=list)


class ResolvePreviewDecision(BaseModel):
    external_id: str
    action: Literal["match", "create_new", "skip", "manual"]
    athlete_id: Optional[int] = None
    source: Optional[ResolveCandidateSourceItem] = None
    note: Optional[str] = None


class ResolvePreviewRequest(BaseModel):
    items: list[ResolvePreviewDecision] = Field(default_factory=list)


class ResolvePreviewSummary(BaseModel):
    matched: int = 0
    create_new: int = 0
    need_manual: int = 0
    skipped: int = 0
    enrich_updates: int = 0


class ResolvePreviewEnrichItem(BaseModel):
    external_id: str
    athlete_id: int
    suggested_patch: SuggestedPatch


class ResolvePreviewCreateItem(BaseModel):
    external_id: str
    payload: BulkAthleteCreateItem


class ResolvePreviewResponse(BaseModel):
    summary: ResolvePreviewSummary
    enrich_updates: list[ResolvePreviewEnrichItem] = Field(default_factory=list)
    create_payloads: list[ResolvePreviewCreateItem] = Field(default_factory=list)


class ReviewSessionCreateRequest(BaseModel):
    source_type: ReviewSourceTypeEnum
    source_ref: str
    meta: dict[str, Any] = Field(default_factory=dict)


class ReviewSessionCreateResponse(BaseModel):
    id: int
    status: ReviewSessionStatusEnum


class ReviewSessionLoadItemsResponse(BaseModel):
    created: int
    updated: int


class ReviewSessionItemResponse(BaseModel):
    id: int
    external_id: str
    status: ReviewItemStatusEnum
    auto_match: bool
    confidence: ReviewConfidenceEnum
    source_payload: dict[str, Any]
    selected_athlete_id: Optional[int] = None
    candidates_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    note: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ReviewSessionItemsListResponse(BaseModel):
    total: int
    items: list[ReviewSessionItemResponse] = Field(default_factory=list)


class ReviewApplyDecisionItem(BaseModel):
    review_item_id: int
    action: ReviewDecisionActionEnum
    athlete_id: Optional[int] = None
    patch: Optional[dict[str, Any]] = None
    note: Optional[str] = None


class ReviewApplyRequest(BaseModel):
    items: list[ReviewApplyDecisionItem] = Field(default_factory=list)


class ReviewApplyResultItem(BaseModel):
    review_item_id: int
    status: ReviewItemStatusEnum
    athlete_id: Optional[int] = None
    created_athlete_id: Optional[int] = None
    updated_fields: list[str] = Field(default_factory=list)


class ReviewApplyErrorItem(BaseModel):
    review_item_id: int
    action: ReviewDecisionActionEnum
    error: str


class ReviewApplyResponse(BaseModel):
    items: list[ReviewApplyResultItem] = Field(default_factory=list)
    errors: list[ReviewApplyErrorItem] = Field(default_factory=list)


class ReviewMarkManualRequest(BaseModel):
    review_item_ids: list[int] = Field(default_factory=list)
    note: Optional[str] = None
