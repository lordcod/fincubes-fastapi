import re
from typing import Annotated, Literal
from uuid import UUID
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.athlete_license import normalize_license


class ImportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProtocolTeam(ImportModel):
    key: str = Field(min_length=1, max_length=100)
    alias: str = Field(min_length=1, max_length=512)
    city: str | None = Field(default=None, max_length=255)
    region: str | None = Field(default=None, max_length=255)


class ProtocolResult(ImportModel):
    key: str = Field(min_length=1, max_length=100)
    event_key: str = Field(min_length=1, max_length=100)
    round: str = Field(default="final", min_length=1, max_length=50)
    dsq_reason: str | None = Field(default=None, max_length=1000)
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

    @field_validator("final_rank")
    @classmethod
    def rank_format(cls, value):
        return normalize_license(value)

    @model_validator(mode="after")
    def status_time(self):
        # Printed values are evidence, not official DSQ/DNS times.
        if self.status in {"DNS", "DNF", "WDR", "DSQ"}:
            printed = {k: getattr(self, k) for k in ("result", "final", "place", "final_rank")
                       if getattr(self, k) is not None}
            if printed:
                self.metadata = {**self.metadata, "printed_values": printed}
            self.result = self.final = self.place = self.final_rank = None
        elif self.status == "DSQ_FINAL":
            printed = {k: getattr(self, k) for k in ("final", "final_rank")
                       if getattr(self, k) is not None}
            if printed:
                self.metadata = {**self.metadata, "printed_final": printed}
            self.final = self.final_rank = None
        elif self.result is None and self.final is None and self.place is None:
            raise ValueError("Performance requires a time or a printed place")
        return self


class ProtocolAthlete(ImportModel):
    key: str = Field(min_length=1, max_length=100)
    team_key: str | None = Field(default=None, min_length=1)
    last_name: str = Field(min_length=1, max_length=100)
    first_name: str = Field(min_length=1, max_length=100)
    birth_year: int = Field(ge=1800, le=2200)
    gender: Literal["M", "F"]
    license: str | None = Field(default=None, max_length=50)
    results: list[ProtocolResult] = Field(default_factory=list)

    _normalize_license = field_validator("license")(normalize_license)


class ProtocolDistance(ImportModel):
    key: str = Field(min_length=1, max_length=100)
    order: int = Field(ge=1)
    stroke: Literal["APNEA", "BIFINS", "IMMERSION", "SURFACE"]
    distance: int = Field(gt=0)
    relay_count: int = Field(default=1, ge=1)
    gender: Literal["M", "F", "X"]
    category: str | None = Field(default=None, max_length=255)
    min_year: int | None = Field(default=None, ge=1800, le=2200)
    max_year: int | None = Field(default=None, ge=1800, le=2200)

    @model_validator(mode="after")
    def years(self):
        if self.min_year is not None and self.max_year is not None and self.min_year > self.max_year:
            raise ValueError("min_year must not exceed max_year")
        return self


class ProtocolLeg(ImportModel):
    athlete_key: str
    order: int = Field(ge=1)
    result: str | None = None
    _time = field_validator("result")(ProtocolResult.time_format.__func__)


class ProtocolRelay(ImportModel):
    key: str = Field(min_length=1, max_length=100)
    event_key: str
    round: str = Field(default="final", min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=512)
    stroke: Literal["APNEA", "BIFINS", "IMMERSION", "SURFACE"]
    distance: int = Field(gt=0)
    relay_count: int = Field(gt=1)
    gender: Literal["M", "F", "X"]
    result: str | None = None
    place: str | None = Field(default=None, max_length=50)
    points: str | None = Field(default=None, max_length=50)
    status: Literal["COMPLETED", "QUALIFIED", "EXH", "DNS", "DNF", "WDR", "DSQ"] = "COMPLETED"
    metadata: dict = Field(default_factory=dict)
    legs: list[ProtocolLeg] = Field(default_factory=list)
    _time = field_validator("result")(ProtocolResult.time_format.__func__)

    @model_validator(mode="after")
    def composition(self):
        orders = [x.order for x in self.legs]
        keys = [x.athlete_key for x in self.legs]
        if len(set(orders)) != len(orders) or len(set(keys)) != len(keys):
            raise ValueError("Relay legs and athletes must be unique")
        if any(x > self.relay_count for x in orders):
            raise ValueError("Relay leg exceeds relay_count")
        if self.status in {"DNS", "DNF", "WDR", "DSQ"}:
            if self.result is not None or self.place is not None:
                self.metadata = {**self.metadata, "printed_values": {"result": self.result, "place": self.place}}
            self.result = self.place = None
        elif self.result is None and self.place is None:
            raise ValueError("Relay requires time or printed place")
        return self


class ProtocolCompetition(ImportModel):
    name: str = Field(min_length=1, max_length=255)
    start_date: date
    end_date: date
    city: str | None = Field(default=None, max_length=255)
    location: str = Field(default="", max_length=255)
    organizer: str = Field(default="", max_length=100)
    course: Literal["LCM", "SCM"] | None = None
    status: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must not precede start_date")
        return self


class PrepareImport(ImportModel):
    type: Literal["prepare"]
    import_id: UUID
    competition_id: int | None = Field(default=None, gt=0)
    competition: ProtocolCompetition | None = None
    mode: Literal["append", "update", "replace"] = "append"
    teams: list[ProtocolTeam] = Field(default_factory=list)
    athletes: list[ProtocolAthlete] = Field(default_factory=list)
    distances: list[ProtocolDistance] = Field(default_factory=list)
    relays: list[ProtocolRelay] = Field(default_factory=list)

    @model_validator(mode="after")
    def references(self):
        if (self.competition_id is None) == (self.competition is None):
            raise ValueError("Supply competition_id or competition")
        groups = [self.teams, self.athletes, self.distances, self.relays,
                  [r for a in self.athletes for r in a.results]]
        if any(len({x.key for x in group}) != len(group) for group in groups):
            raise ValueError("Keys must be unique within each record type")
        teams = {t.key for t in self.teams}
        athletes = {a.key: a for a in self.athletes}
        events = {d.key: d for d in self.distances}
        identities = set()
        for athlete in self.athletes:
            if athlete.team_key is not None and athlete.team_key not in teams:
                raise ValueError("Unknown team_key")
            for result in athlete.results:
                event = events.get(result.event_key)
                if event is None or (event.stroke, event.distance, event.relay_count) != (result.stroke, result.distance, 1):
                    raise ValueError("Result must reference a matching individual event")
                identity = (athlete.key, event.stroke, event.distance, event.category, event.min_year, event.max_year, result.round)
                if identity in identities:
                    raise ValueError("Duplicate athlete/event/round result")
                identities.add(identity)
                if event.gender != athlete.gender:
                    raise ValueError("Result gender differs from event")
        relay_identities = set()
        for relay in self.relays:
            event = events.get(relay.event_key)
            if event is None or (event.stroke, event.distance, event.relay_count, event.gender) != (relay.stroke, relay.distance, relay.relay_count, relay.gender):
                raise ValueError("Relay must reference a matching relay event")
            identity = (relay.name, event.stroke, event.distance, event.relay_count, event.gender, event.category, event.min_year, event.max_year, relay.round)
            if identity in relay_identities:
                raise ValueError("Duplicate relay/event/round")
            relay_identities.add(identity)
            if any(leg.athlete_key not in athletes for leg in relay.legs):
                raise ValueError("Unknown relay athlete_key")
        return self


class ExistingAthlete(ImportModel):
    action: Literal["existing"]
    athlete_id: int = Field(gt=0)


class NewAthlete(ImportModel):
    action: Literal["create"]


class OmitRecord(ImportModel):
    action: Literal["skip", "defer"]
    reason: str = Field(min_length=1, max_length=1000)


class TeamFields(ImportModel):
    club: str | None = Field(default=None, max_length=512)
    city: str | None = Field(default=None, max_length=255)
    region: str | None = Field(default=None, max_length=255)


class FinishImport(ImportModel):
    type: Literal["finish"]
    import_id: UUID
    competition_id: int | None = Field(default=None, gt=0)
    decisions: dict[str, Annotated[ExistingAthlete | NewAthlete | OmitRecord, Field(discriminator="action")]] = Field(default_factory=dict)
    teams: dict[str, TeamFields] = Field(default_factory=dict)
    results: dict[str, OmitRecord] = Field(default_factory=dict)
    relays: dict[str, OmitRecord] = Field(default_factory=dict)
    resume: list[str] = Field(default_factory=list)
    result_ids: dict[str, int] = Field(default_factory=dict)
    relay_ids: dict[str, int] = Field(default_factory=dict)
    replace_token: str | None = None


ProtocolImportRequest = Annotated[PrepareImport | FinishImport, Field(discriminator="type")]
