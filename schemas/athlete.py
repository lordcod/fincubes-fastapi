from tortoise.contrib.pydantic import pydantic_model_creator
from models.models import Athlete


AthleteIn_Pydantic = pydantic_model_creator(Athlete, exclude_readonly=True)
Athlete_Pydantic = pydantic_model_creator(Athlete)
