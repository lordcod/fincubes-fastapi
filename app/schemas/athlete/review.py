from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.athlete.athlete import Athlete_Pydantic


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
    reasons: list[str] = Field(default_factory=list)
    suggested_patch: Optional[SuggestedPatch] = None


class ResolveCandidatesResponseItem(BaseModel):
    external_id: str
    candidates: list[ResolveCandidateItem] = Field(default_factory=list)
    auto_match: bool = False


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
