import re
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.location.location import LocationObjectCreate, RequiredLocationField


class ImportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProtocolTeam(ImportModel):
    key: str = Field(min_length=1, max_length=100)
    alias: str = Field(min_length=1, max_length=512)
    city: str | None = Field(default=None, max_length=255)
    region: str | None = Field(default=None, max_length=255)


class ProtocolResult(ImportModel):
    stroke: Literal["APNEA", "BIFINS", "IMMERSION", "SURFACE"]
    distance: int = Field(gt=0)
    result: str | None = None
    final: str | None = None
    place: str | None = Field(default=None, max_length=50)
    final_rank: str | None = Field(default=None, max_length=50)
    points: str | None = Field(default=None, max_length=50)
    record: str | None = Field(default=None, max_length=255)
    status: Literal["COMPLETED", "QUALIFIED", "EXH", "DNS", "DNF", "WDR", "DSQ", "DSQ_FINAL"] = "COMPLETED"
    metadata: dict = Field(default_factory=dict)

    @field_validator("result", "final")
    @classmethod
    def time_format(cls, value):
        if value is None:
            return None
        if not re.fullmatch(r"(?:(?:[0-5]?\d):)?[0-5]?\d[.,]\d{2}", value):
            raise ValueError("Time must be mm:ss.SS or ss.SS, with exactly two decimal digits")
        if not any(c in "123456789" for c in value):
            raise ValueError("Time must be positive")
        return value.replace(",", ".")

    @model_validator(mode="after")
    def status_time(self):
        if self.status in {"DNS", "DNF", "WDR", "DSQ"}:
            if any(v is not None for v in (self.result, self.final, self.place, self.final_rank)):
                raise ValueError("This status has no official time or place; preserve printed values in metadata")
        elif self.status == "DSQ_FINAL":
            if self.final is not None or self.final_rank is not None:
                raise ValueError("Disqualified final cannot have an official final time or rank")
        elif self.result is None and self.final is None:
            raise ValueError("Completed performance requires a time")
        if self.place is not None and self.result is None:
            raise ValueError("Place requires result time")
        if self.final_rank is not None and self.final is None:
            raise ValueError("Final rank requires final time")
        return self


class ProtocolAthlete(ImportModel):
    key: str = Field(min_length=1, max_length=100)
    team_key: str = Field(min_length=1)
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    birth_year: int = Field(ge=1800, le=2200)
    gender: Literal["M", "F"]
    license: str | None = Field(default=None, max_length=50)
    results: list[ProtocolResult] = Field(min_length=1)


class PrepareImport(ImportModel):
    type: Literal["prepare"]
    import_id: UUID
    competition_id: int
    teams: list[ProtocolTeam] = Field(min_length=1)
    athletes: list[ProtocolAthlete] = Field(min_length=1)

    @model_validator(mode="after")
    def references(self):
        team_keys = {t.key for t in self.teams}
        if len(team_keys) != len(self.teams) or len({a.key for a in self.athletes}) != len(self.athletes):
            raise ValueError("Team and athlete keys must be unique")
        if any(a.team_key not in team_keys for a in self.athletes):
            raise ValueError("Unknown team_key")
        return self


class ExistingLocation(ImportModel):
    action: Literal["existing"]
    location_id: UUID
    required: set[RequiredLocationField] = Field(default_factory=set)


class NewLocation(ImportModel):
    action: Literal["create"]
    location: LocationObjectCreate


class LocationsImport(ImportModel):
    type: Literal["locations"]
    import_id: UUID
    decisions: dict[str, Annotated[ExistingLocation | NewLocation, Field(discriminator="action")]] = Field(default_factory=dict)


class ExistingAthlete(ImportModel):
    action: Literal["existing"]
    athlete_id: int = Field(gt=0)


class NewAthlete(ImportModel):
    action: Literal["create"]


class FinishImport(ImportModel):
    type: Literal["finish"]
    import_id: UUID
    decisions: dict[str, Annotated[ExistingAthlete | NewAthlete, Field(discriminator="action")]] = Field(default_factory=dict)


ProtocolImportRequest = Annotated[PrepareImport | LocationsImport | FinishImport, Field(discriminator="type")]
