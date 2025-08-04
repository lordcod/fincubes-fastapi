from typing import List, Optional, cast

from pydantic import BaseModel

from app.models.competition.result import Result
from app.schemas import create_pydantic_model
from app.schemas.competition.competition import Competition_Pydantic

ResultDepth0_Pydantic = create_pydantic_model(Result)


class UserPerformance(ResultDepth0_Pydantic):
    top_rank: Optional[int] = None
    best: bool = False


class UserCompetitionResult(BaseModel):
    competition: Competition_Pydantic
    performances: List[UserPerformance]


class UserAthleteResults(BaseModel):
    id: int
    results: List[UserCompetitionResult]
