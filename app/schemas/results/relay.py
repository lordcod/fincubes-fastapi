from pydantic import computed_field, field_validator

from app.models.competition.relay_leg import RelayLeg
from app.models.competition.relay_result import RelayResult
from app.schemas import create_pydantic_model
from app.shared.enums.enums import EventTypeEnum


_RelayResultIn_Pydantic = create_pydantic_model(
    RelayResult,
    exclude_readonly=True,
    exclude=("competition",),
)


class RelayResultIn_Pydantic(_RelayResultIn_Pydantic):
    relay_count: int = 1
    status: str = "COMPLETED"

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("name must not be empty")
        return value

    @field_validator("distance")
    @classmethod
    def validate_distance(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("distance must be greater than 0")
        return value

_RelayResult_Pydantic = create_pydantic_model(
    RelayResult,
    exclude=("competition", "legs"),
)


class RelayResult_Pydantic(_RelayResult_Pydantic):
    competition_id: int
    event_type: EventTypeEnum = EventTypeEnum.RELAY

    @computed_field
    @property
    def total_distance(self) -> int:
        return self.distance * self.relay_count


_RelayLegIn_Pydantic = create_pydantic_model(
    RelayLeg,
    exclude_readonly=True,
    exclude=("relay_result", "athlete"),
)


class RelayLegIn_Pydantic(_RelayLegIn_Pydantic):
    athlete_id: int

    @field_validator("order")
    @classmethod
    def validate_order(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("order must be greater than 0")
        return value


_RelayLeg_Pydantic = create_pydantic_model(
    RelayLeg,
    exclude=("relay_result", "athlete"),
)


class RelayLeg_Pydantic(_RelayLeg_Pydantic):
    relay_result_id: int
    athlete_id: int


class RelayResultCreate(RelayResultIn_Pydantic):
    competition_id: int
    legs: list[RelayLegIn_Pydantic]


class RelayResultWithLegs(RelayResult_Pydantic):
    legs: list[RelayLeg_Pydantic]
