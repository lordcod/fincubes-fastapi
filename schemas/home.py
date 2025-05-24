from models.models import RecentEvent, TopAthlete
from tortoise.contrib.pydantic import pydantic_model_creator

from schemas import with_nested
from schemas.athlete import Athlete_Pydantic
from schemas.competition import Competition_Pydantic


TopAthleteIn = pydantic_model_creator(TopAthlete, exclude_readonly=True)
TopAthleteOut = with_nested(pydantic_model_creator(TopAthlete),
                            athlete=Athlete_Pydantic)

RecentEventIn = pydantic_model_creator(RecentEvent, exclude_readonly=True)
RecentEventOut = RecentEventOut = with_nested(
    pydantic_model_creator(RecentEvent),
    competition=Competition_Pydantic
)
