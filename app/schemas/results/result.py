from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from app.models.competition.result import Result
from app.schemas import create_pydantic_model, with_nested
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.schemas.competition.competition import Competition_Pydantic
from app.shared.enums.enums import EventTypeEnum
from app.shared.utils.flexible_time import FlexibleTime

_ResultDepth0_Pydantic = create_pydantic_model(Result)


class ResultDepth0_Pydantic(_ResultDepth0_Pydantic):
    event_type: EventTypeEnum = EventTypeEnum.INDIVIDUAL


ResultIn_Pydantic = with_nested(
    create_pydantic_model(Result, exclude_readonly=True,
                          exclude=('resolved_time', ))
)
_Result_Pydantic = with_nested(
    ResultDepth0_Pydantic,
    athlete=Athlete_Pydantic,
    competition=Competition_Pydantic,
    best=(Optional[FlexibleTime], None),
)


class Result_Pydantic(_Result_Pydantic):
    @classmethod
    async def from_tortoise_orm(cls, result: Result):
        await result.fetch_related("athlete__location_object", "competition")
        result_data = (await ResultDepth0_Pydantic.from_tortoise_orm(result)).model_dump()
        athlete = await Athlete_Pydantic.from_tortoise_orm(result.athlete)
        competition = await Competition_Pydantic.from_tortoise_orm(result.competition)
        return cls.model_validate(
            {
                **result_data,
                "athlete": athlete,
                "competition": competition,
                "best": None,
            }
        )

    @classmethod
    async def from_queryset(cls, queryset):
        rows = await queryset.prefetch_related(
            "athlete__location_object",
            "competition",
        )
        return [await cls.from_tortoise_orm(row) for row in rows]


class BulkCreateResult(BaseModel):
    competition_id: int
    athlete_id: int
    results: List[ResultIn_Pydantic]


class BulkCreateResultExceptionResponse(BaseModel):
    exception: bool
    name: str
    description: str
    input: BulkCreateResult


class BulkCreateResultResponse(BaseModel):
    results: Optional[List[Result_Pydantic]] = None
    errors: Optional[List[BulkCreateResultExceptionResponse]] = None
