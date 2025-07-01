from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.athlete.top_athlete import TopAthlete
from app.schemas import with_nested
from app.schemas.athlete.athlete import Athlete_Pydantic

TopAthleteIn = pydantic_model_creator(TopAthlete, exclude_readonly=True)
TopAthleteOut = with_nested(
    pydantic_model_creator(TopAthlete),
    athlete=Athlete_Pydantic
)
