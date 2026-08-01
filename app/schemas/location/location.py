from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


RequiredLocationField = Literal["city", "region"]


class LocationAliasesAdd(BaseModel):
    aliases: list[str] = Field(min_length=1)
    required: set[RequiredLocationField] = Field(default_factory=set)

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, values: list[str]) -> list[str]:
        cleaned = []
        for value in values:
            stripped = value.strip()
            if not stripped:
                raise ValueError("alias cannot be empty")
            if len(stripped) > 512:
                raise ValueError("alias cannot be longer than 512 characters")
            cleaned.append(stripped)
        if len(set(cleaned)) != len(cleaned):
            raise ValueError("aliases must be unique")
        return cleaned


class LocationAliasOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location_object_id: UUID
    alias: str
    required: list[RequiredLocationField] = Field(default_factory=list)


class LocationAliasUpdate(BaseModel):
    alias: Optional[str] = Field(default=None, min_length=1, max_length=512)
    required: Optional[set[RequiredLocationField]] = None

    @field_validator("alias")
    @classmethod
    def strip_alias(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("alias cannot be empty")
        return stripped


class LocationObjectCreate(BaseModel):
    aliases: list[str] = Field(min_length=1)
    club: Optional[str] = Field(default=None, max_length=512)
    city: Optional[str] = Field(default=None, max_length=255)
    region: str = Field(min_length=1, max_length=255)
    required: set[RequiredLocationField] = Field(default_factory=set)

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, values: list[str]) -> list[str]:
        return LocationAliasesAdd(aliases=values).aliases

    @field_validator("region")
    @classmethod
    def strip_region(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("region cannot be empty")
        return stripped

    @field_validator("club", "city")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class LocationObjectUpdate(BaseModel):
    club: Optional[str] = Field(default=None, max_length=512)
    city: Optional[str] = Field(default=None, max_length=255)
    region: Optional[str] = Field(default=None, min_length=1, max_length=255)

    @field_validator("region")
    @classmethod
    def strip_region(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("region cannot be empty")
        return stripped

    @field_validator("club", "city")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class LocationObjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    club: Optional[str] = None
    city: Optional[str] = None
    region: str
    aliases: list[LocationAliasOut] = Field(default_factory=list)


class LocationCatalogItem(BaseModel):
    id: UUID
    alias_id: Optional[UUID] = None
    alias: Optional[str] = None
    club: Optional[str] = None
    city: Optional[str] = None
    region: str
    required: list[RequiredLocationField] = Field(default_factory=list)


class LocationEntitySearchItem(BaseModel):
    id: UUID
    name: str
    exact_match: bool
    similarity: float = Field(ge=0, le=1)


class LocationResolveRequest(BaseModel):
    alias: str = Field(min_length=1, max_length=512)
    city: Optional[str] = Field(default=None, max_length=255)
    region: Optional[str] = Field(default=None, max_length=255)

    @field_validator("alias", "city", "region")
    @classmethod
    def strip_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class LocationResolveResult(BaseModel):
    id: UUID
    alias_id: UUID
    alias: str
    club: Optional[str] = None
    city: Optional[str] = None
    region: str
    required: list[RequiredLocationField] = Field(default_factory=list)


class LocationMergeRequest(BaseModel):
    target_location_id: UUID
    move_aliases: bool = True
    delete_source: bool = True


class LocationMergePreview(BaseModel):
    source: LocationObjectOut
    target: LocationObjectOut
    athletes_to_move: int
    aliases_to_move: list[str] = Field(default_factory=list)
    duplicate_aliases: list[str] = Field(default_factory=list)


class LocationMergeResult(BaseModel):
    target: LocationObjectOut
    deleted_source_id: Optional[UUID] = None
    moved_athletes: int
    moved_aliases: int
    duplicate_aliases: list[str] = Field(default_factory=list)
