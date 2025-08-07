from typing import List, Optional, cast

from pydantic import BaseModel
from app.schemas.competition.competition import Competition_Pydantic
from app.schemas.results.result import ResultDepth0_Pydantic


class UserPerformance(ResultDepth0_Pydantic):
    top_rank: Optional[int] = None
    best: bool = False


class UserCompetitionResult(BaseModel):
    competition: Competition_Pydantic
    performances: List[UserPerformance]


class UserAthleteResults(BaseModel):
    id: int
    results: List[UserCompetitionResult]
