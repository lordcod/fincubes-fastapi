from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import Result
from app.repositories.sa.top_results import prepare_columns
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.schemas.competition.competition import Competition_Pydantic
from app.schemas.results.result import ResultDepth0_Pydantic
from app.shared.enums.enums import GenderEnum


class AgeCategory(BaseModel):
    name: str
    id: str
    min_age: Optional[int] = Field(default=None, ge=0)
    max_age: Optional[int] = Field(default=None, ge=0)


class RandomTop(BaseModel):
    stroke: str
    distance: int
    category: AgeCategory
    gender: GenderEnum


class BestFullResult(BaseModel):
    result: ResultDepth0_Pydantic
    athlete: Athlete_Pydantic
    competition: Competition_Pydantic
    row_num: int


AthleteTopResponse = Dict[str, List[BestFullResult]]


class TopResponse(BaseModel):
    results: List[BestFullResult]


def parse_best_full_result(row: dict) -> BestFullResult:
    return BestFullResult(
        result=prepare_columns(Result, row, 'result'),
        athlete=prepare_columns(Athlete, row, 'athlete'),
        competition=prepare_columns(Competition, row, 'competition'),
        row_num=row["row_num"],
    )
