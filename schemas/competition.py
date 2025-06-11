from models.models import Competition
from tortoise.contrib.pydantic import pydantic_model_creator

# Models

CompetitionIn_Pydantic = pydantic_model_creator(Competition, exclude_readonly=True)
Competition_Pydantic = pydantic_model_creator(Competition)
