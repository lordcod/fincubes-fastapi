from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.athlete.athlete import Athlete

AthleteIn_Pydantic = pydantic_model_creator(Athlete, exclude_readonly=True)
Athlete_Pydantic = pydantic_model_creator(Athlete)
