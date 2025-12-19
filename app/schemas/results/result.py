from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from app.models.competition.result import CompetitionResult, CompetitionStage
from app.schemas import create_pydantic_model, with_nested
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.schemas.competition.competition import Competition_Pydantic
from app.shared.utils.flexible_time import FlexibleTime


CompetitionStage_Pydantic = create_pydantic_model(CompetitionStage)


ResultDepthNullStages_Pydantic = create_pydantic_model(CompetitionResult)
ResultDepth0_Pydantic = with_nested(
    create_pydantic_model(CompetitionResult),
    stages=List[CompetitionStage_Pydantic]
)
ResultIn_Pydantic = with_nested(
    create_pydantic_model(CompetitionResult, exclude_readonly=True,
                          exclude=('resolved_time', )),
    stages=List[CompetitionStage_Pydantic]
)
Result_Pydantic = with_nested(
    create_pydantic_model(CompetitionResult),
    stages=List[CompetitionStage_Pydantic],
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
