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
Result_Pydantic = with_nested(
    ResultDepth0_Pydantic,
    athlete=Athlete_Pydantic,
    competition=Competition_Pydantic,
    best=(Optional[FlexibleTime], None),
)


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
