from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


RequiredLocationField = Literal["city", "region"]


class LocationAliasesAdd(BaseModel):
    aliases: list[str] = Field(min_length=1)

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
    aliases: Optional[list[str]] = None
    club: Optional[str] = Field(default=None, max_length=512)
    city: Optional[str] = Field(default=None, max_length=255)
    region: Optional[str] = Field(default=None, min_length=1, max_length=255)
    required: Optional[set[RequiredLocationField]] = None

    @field_validator("aliases")
    @classmethod
    def validate_aliases(cls, values: Optional[list[str]]) -> Optional[list[str]]:
        if values is None:
            return None
        return LocationAliasesAdd(aliases=values).aliases

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
    aliases: list[str] = Field(default_factory=list)
    club: Optional[str] = None
    city: Optional[str] = None
    region: str
    required: list[RequiredLocationField] = Field(default_factory=list)


class LocationCatalogItem(LocationObjectOut):
    pass


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
    alias: str
    club: Optional[str] = None
    city: Optional[str] = None
    region: str
    required: list[RequiredLocationField] = Field(default_factory=list)
