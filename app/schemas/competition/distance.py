from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
    field_validator,
)
from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.competition.distance import Distance
from app.schemas import with_nested
from app.schemas.competition.competition import Competition_Pydantic

_DistanceIn_Pydantic = pydantic_model_creator(
    Distance,
    exclude_readonly=True,
)


class DistanceIn_Pydantic(_DistanceIn_Pydantic):
    @field_validator("distance", "relay_count")
    @classmethod
    def validate_positive_distance_values(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("must be greater than 0")
        return value


_Distance_Pydantic = pydantic_model_creator(Distance)


class DistanceWithTotal_Pydantic(_Distance_Pydantic):
    @computed_field
    @property
    def total_distance(self) -> int:
        return self.distance * self.relay_count


Distance_Pydantic = with_nested(
    DistanceWithTotal_Pydantic,
    competition=Competition_Pydantic,
)


class DistanceOrderUpdate_Pydantic(BaseModel):
    id: int
    order: int

    model_config = ConfigDict(from_attributes=True)
