from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator
from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.athlete.athlete import Athlete
from app.schemas import create_pydantic_model, with_nested

AthleteIn_Pydantic = pydantic_model_creator(Athlete, exclude_readonly=True)
Athlete_Pydantic = create_pydantic_model(Athlete)


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


AthleteDetailed_Pydantic = with_nested(
    create_pydantic_model(Athlete),
    occupied_places_count=(int, Field(0, description="По умолчанию 0")),
    competitions_count=(int, Field(0, description="По умолчанию 0")),
)


AthleteWithStatus_Pydantic = with_nested(
    create_pydantic_model(Athlete),
    status=str
)
