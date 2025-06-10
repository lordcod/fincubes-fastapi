from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from models.flexible_time import FlexibleTime


class RandomTop(BaseModel):
    stroke: str
    distance: int


class Athlete(BaseModel):
    id: int
    first_name: str
    last_name: str
    gender: str
    birth_year: str


class Competition(BaseModel):
    id: int
    name: str
    start_date: date
    end_date: date
    date: str


class Result(BaseModel):
    id: int
    result: Optional[FlexibleTime]
    final: Optional[FlexibleTime]
    competition_id: int
    athlete_id: int
    stroke: str
    distance: int


class BestFullResult(BaseModel):
    result: Result
    athlete: Athlete
    competition: Competition
    best: Optional[FlexibleTime]
    row_num: int


class TopResponse(BaseModel):
    results: List[BestFullResult]


def parse_best_full_result(row: dict) -> BestFullResult:
    return BestFullResult(
        result=Result(
            id=row["result_id"],
            result=FlexibleTime.validate(row.get("result_result")),
            final=row.get("result_final") and FlexibleTime.validate(
                row.get("result_final")),
            competition_id=row["competition_id"],
            athlete_id=row["athlete_id"],
            stroke=row["stroke"],
            distance=row["distance"]
        ),
        athlete=Athlete(
            id=row['athlete_id'],
            first_name=row["athlete_first_name"],
            last_name=row["athlete_last_name"],
            gender=row["athlete_gender"],
            birth_year=row.get("athlete_birth_year")
        ),
        competition=Competition(
            id=row["competition_id"],
            name=row["competition_name"],
            date=row["competition_date"],
            start_date=row["competition_start_date"],
            end_date=row["competition_end_date"],
        ),
        best=FlexibleTime.validate(row["best"]),
        row_num=row["row_num"]
    )
