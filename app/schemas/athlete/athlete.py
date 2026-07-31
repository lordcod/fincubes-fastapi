from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.athlete.athlete import Athlete
from app.schemas.location.location import LocationObjectOut


class AthleteIn_Pydantic(BaseModel):
    last_name: str = Field(max_length=100)
    first_name: str = Field(max_length=100)
    birth_year: int | str
    location_object_id: Optional[UUID] = None
    license: Optional[str] = Field(default=None, max_length=50)
    gender: str = Field(min_length=1, max_length=1)
    avatar_url: Optional[str] = Field(default=None, max_length=250)
    is_top: bool = False


class Athlete_Pydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    last_name: str
    first_name: str
    birth_year: str
    location_object_id: Optional[UUID] = None
    location: Optional[LocationObjectOut] = None
    club: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    license: Optional[str] = None
    gender: str
    avatar_url: Optional[str] = None
    is_top: bool = False

    @classmethod
    async def from_tortoise_orm(cls, athlete: Athlete):
        location = await _get_athlete_location(athlete)
        return cls.model_validate(
            {
                "id": athlete.id,
                "created_at": athlete.created_at,
                "updated_at": athlete.updated_at,
                "last_name": athlete.last_name,
                "first_name": athlete.first_name,
                "birth_year": athlete.birth_year,
                "location_object_id": athlete.location_object_id,
                "location": location,
                "club": location.club if location else None,
                "city": location.city if location else None,
                "region": location.region if location else None,
                "license": athlete.license,
                "gender": athlete.gender,
                "avatar_url": athlete.avatar_url,
                "is_top": athlete.is_top,
            }
        )

    @classmethod
    async def from_queryset(cls, queryset):
        rows = await queryset.prefetch_related("location_object")
        return [await cls.from_tortoise_orm(row) for row in rows]


async def _get_athlete_location(athlete: Athlete):
    if athlete.location_object_id is None:
        return None
    location = getattr(athlete, "_location_object", None)
    if location is None:
        location = await athlete.location_object
    return LocationObjectOut.model_validate(location)


class AthleteCreateRequest(BaseModel):
    """Backward-compatible athlete payload with an optional normalized location."""

    model_config = ConfigDict(extra="forbid")

    last_name: str = Field(max_length=100)
    first_name: str = Field(max_length=100)
    birth_year: int = Field(ge=1000, le=9999)
    gender: str = Field(min_length=1, max_length=1)
    alias: Optional[str] = Field(default=None, max_length=512)
    club: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=255)
    region: Optional[str] = Field(default=None, max_length=255)
    license: Optional[str] = Field(default=None, max_length=50)
    avatar_url: Optional[str] = Field(default=None, max_length=250)
    is_top: bool = False

    @field_validator("gender")
    @classmethod
    def normalize_gender(cls, value: str) -> str:
        return value.upper()

    @field_validator("alias", "club", "city", "region", "license", "avatar_url")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class AthleteDetailed_Pydantic(Athlete_Pydantic):
    occupied_places_count: int = Field(0, description="Default is 0")
    competitions_count: int = Field(0, description="Default is 0")


class AthleteWithStatus_Pydantic(Athlete_Pydantic):
    status: str
