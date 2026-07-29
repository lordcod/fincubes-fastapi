from typing import List, Optional

from pydantic import BaseModel
from app.schemas.competition.competition import Competition_Pydantic
from app.schemas.results.result import ResultDepth0_Pydantic
from app.shared.utils.flexible_time import FlexibleTime


class UserPerformance(ResultDepth0_Pydantic):
    best: bool = False
    relay_count: int = 1
    total_distance: int
    name: Optional[str] = None
    split_result: Optional[FlexibleTime] = None
    relay_order: Optional[int] = None
    relay_leg_id: Optional[int] = None
    leg_metadata: Optional[dict | list] = None


class UserCompetitionResult(BaseModel):
    competition: Competition_Pydantic
    performances: List[UserPerformance]


class UserAthleteResults(BaseModel):
    id: int
    results: List[UserCompetitionResult]
