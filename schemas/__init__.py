import re
import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel
from typing import Any
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler

# FlexibleTime class


class FlexibleTime(datetime.time):
    time_regex = re.compile(r'(\d+):(\d{1,2})[.,](\d{1,2})')

    @classmethod
    def validate(cls, value: Any) -> 'FlexibleTime':
        if not value and isinstance(value, (bool, int, str)):
            return cls()

        if isinstance(value, FlexibleTime):
            return value

        if isinstance(value, datetime.timedelta):
            total_seconds = int(value.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            hundredths = round(value.microseconds / 10000)
            return cls(hour=0, minute=minutes, second=seconds, microsecond=hundredths * 10000)

        if isinstance(value, datetime.time):
            return cls(hour=value.hour, minute=value.minute, second=value.second, microsecond=value.microsecond)

        if not isinstance(value, str):
            raise TypeError(
                f"Unsupported type for FlexibleTime: {type(value)}")

        match = cls.time_regex.match(value.strip().replace(',', '.'))
        if not match:
            raise ValueError(f"Invalid time format: {value}")

        minutes, seconds, hundredths = match.groups()
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0
        hundredths = int(hundredths) if hundredths else 0

        return cls(hour=0, minute=minutes, second=seconds, microsecond=hundredths*10_000)

    def __str__(self) -> str:
        if self.hour:
            return f"{self.hour}:{self.minute:02}:{self.second:02}.{int(self.microsecond / 10000):02}"
        return f"{self.minute:02}:{self.second:02}.{int(self.microsecond / 10000):02}"

    def __repr__(self) -> str:
        return f'"{self}"'  # For JSON encoding

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            python_schema=core_schema.no_info_plain_validator_function(
                cls.validate),
            json_schema=core_schema.no_info_plain_validator_function(
                cls.validate),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v)),
        )


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
        orm_mode = True


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
        orm_mode = True


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
        orm_mode = True
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
