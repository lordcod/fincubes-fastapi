from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.athlete.athlete import Athlete_Pydantic
from app.schemas.location.location import AthleteLocationCreate


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
    location: Optional[AthleteLocationCreate] = None


class BulkAthleteCreateRequest(BaseModel):
    items: list[BulkAthleteCreateItem] = Field(default_factory=list)


class BulkAthleteCreateResultItem(BaseModel):
    external_id: Optional[str] = None
    athlete: Athlete_Pydantic


class BulkAthleteCreateResponse(BaseModel):
    items: list[BulkAthleteCreateResultItem] = Field(default_factory=list)
