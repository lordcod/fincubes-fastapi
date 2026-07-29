from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


RequiredLocationField = Literal["city", "region"]


class LocationAliasesAdd(BaseModel):
    aliases: list[str] = Field(min_length=1)

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("alias не может быть пустым")
        if any(len(value) > 512 for value in values):
            raise ValueError("alias не может быть длиннее 512 символов")
        if len(set(values)) != len(values):
            raise ValueError("aliases не должны повторяться")
        return values


class LocationObjectCreate(BaseModel):
    aliases: list[str] = Field(min_length=1)
    club: Optional[str] = Field(default=None, max_length=512)
    club_id: Optional[UUID] = None
    city: Optional[str] = Field(default=None, max_length=255)
    city_id: Optional[UUID] = None
    region: str = Field(min_length=1, max_length=255)
    region_id: Optional[UUID] = None
    required: set[RequiredLocationField] = Field(default_factory=set)

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("alias не может быть пустым")
        if any(len(value) > 512 for value in values):
            raise ValueError("alias не может быть длиннее 512 символов")
        if len(set(values)) != len(values):
            raise ValueError("aliases не должны повторяться")
        return values

    @field_validator("region")
    @classmethod
    def strip_region(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("значение не может быть пустым")
        return stripped

    @field_validator("club", "city")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @model_validator(mode="after")
    def validate_names_and_ids(self):
        if self.club is None and self.club_id is not None:
            raise ValueError("club_id нельзя указывать без club")
        if self.city is None and self.city_id is not None:
            raise ValueError("city_id нельзя указывать без city")
        return self


class LocationObjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    aliases: list[str] = Field(default_factory=list)
    club: Optional[str] = None
    club_id: Optional[UUID] = None
    city: Optional[str] = None
    city_id: Optional[UUID] = None
    region: str
    region_id: UUID
    required: list[RequiredLocationField] = Field(default_factory=list)


class LocationCatalogItem(BaseModel):
    id: UUID
    aliases: list[str] = Field(default_factory=list)
    club: Optional[str] = None
    club_id: Optional[UUID] = None
    city: Optional[str] = None
    city_id: Optional[UUID] = None
    region: str
    region_id: UUID
    required: list[RequiredLocationField] = Field(default_factory=list)


class LocationEntitySearchItem(BaseModel):
    id: UUID
    name: str
    exact_match: bool
    similarity: float = Field(ge=0, le=1)


class AthleteLocationCreate(BaseModel):
    location_id: UUID
    alias: str = Field(min_length=1, max_length=512)

    @field_validator("alias")
    @classmethod
    def validate_alias(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("значение не может быть пустым")
        return value


class AthleteLocationOut(BaseModel):
    id: int
    athlete_id: int
    alias: str
    location: LocationObjectOut
