import json
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.competition.competition import Competition
from app.repositories.sa.utils import prepare_columns
from app.schemas.athlete.athlete import Athlete_Pydantic
from app.schemas.competition.competition import Competition_Pydantic
from app.schemas.location.location import LocationObjectOut
from app.schemas.results.result import ResultDepth0_Pydantic
from app.shared.enums.enums import EventTypeEnum, GenderEnum


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
    result_fields = set(ResultDepth0_Pydantic.model_fields)
    result_data = {
        field_name: value
        for name, value in row.items()
        if name.startswith("result_")
        and (field_name := name.removeprefix("result_")) in result_fields
    }
    result_data["event_type"] = EventTypeEnum(
        result_data.get(
            "event_type",
            EventTypeEnum.INDIVIDUAL,
        )
    )
    metadata = result_data.get("metadata")
    if isinstance(metadata, str):
        result_data["metadata"] = json.loads(metadata)

    athlete_fields = set(Athlete_Pydantic.model_fields)
    athlete_data = {
        field_name: value
        for name, value in row.items()
        if name.startswith("athlete_")
        and (field_name := name.removeprefix("athlete_")) in athlete_fields
    }

    location_id = row.get("location_id")
    location = None
    if location_id is not None:
        location = LocationObjectOut.model_validate(
            {
                "id": location_id,
                "club": row.get("location_club"),
                "city": row.get("location_city"),
                "region": row.get("location_region"),
                "aliases": [],
            }
        )
        athlete_data["location"] = location
        athlete_data["club"] = location.club
        athlete_data["city"] = location.city
        athlete_data["region"] = location.region

    return BestFullResult(
        result=ResultDepth0_Pydantic.model_validate(result_data),
        athlete=Athlete_Pydantic.model_validate(athlete_data),
        competition=prepare_columns(Competition, row, 'competition'),
        row_num=row["row_num"],
    )
