from typing import List, Optional

from pydantic import BaseModel

from app.shared.utils.flexible_time import FlexibleTime


class UserPerformance(BaseModel):
    stroke: str
    distance: int
    result: Optional[FlexibleTime] = None
    final: Optional[FlexibleTime] = None
    place: Optional[str | int] = None
    final_rank: Optional[str] = None
    points: Optional[str | int] = None
    top_rank: Optional[int] = None
    record: Optional[str] = None
    best: bool = False
    dsq: bool = False
    dsq_final: bool = False

    class Config:
        json_encoders = {FlexibleTime: lambda v: str(v)}


class UserCompetitionResult(BaseModel):
    date: str
    competition: str
    id: int
    performances: List[UserPerformance]


class UserAthleteResults(BaseModel):
    id: int
    results: List[UserCompetitionResult]
