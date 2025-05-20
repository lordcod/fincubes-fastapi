import re
import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel
from .flexible_time import FlexibleTime


# Models
class CompetitionIn_Pydantic(BaseModel):
    name: str
    date: str
    location: str
    organizer: str
    status: Optional[Literal['ALL', 'REG', 'COM', 'MUN', 'OTH']] = None
    links: list
    start_date: datetime.date
    end_date: datetime.date

    class Config:
        from_attributes = True


class Competition_Pydantic(CompetitionIn_Pydantic):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class AthleteIn_Pydantic(BaseModel):
    last_name: str
    first_name: str
    birth_year: str
    club: str
    city: Optional[str] = None
    license: str
    gender: str

    class Config:
        from_attributes = True


class Athlete_Pydantic(AthleteIn_Pydantic):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class ResultIn_Pydantic(BaseModel):
    stroke: str
    distance: int
    result: Optional[FlexibleTime] = None
    final: Optional[FlexibleTime] = None
    place: Optional[str | int] = None
    final_rank: Optional[str] = None
    points: Optional[str | int] = None
    record: Optional[str] = None
    dsq: bool = False
    dsq_final: bool = False
    athlete: Optional[Athlete_Pydantic] = None
    competition: Optional[Competition_Pydantic] = None
    best: Optional[FlexibleTime] = None

    class Config:
        from_attributes = True
        json_encoders = {FlexibleTime: lambda v: str(v)}


class Result_Pydantic(ResultIn_Pydantic):
    id: int
    athlete_id: int
    competition_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime


class Top_Pydantic(BaseModel):
    stroke: str
    distance: int
    results: List[Result_Pydantic]


class RandomTop_Pydantic(BaseModel):
    stroke: str
    distance: int


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
    athlete_id: int
    results: List[UserCompetitionResult]


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
