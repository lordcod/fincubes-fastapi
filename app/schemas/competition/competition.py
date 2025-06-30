
from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.competition.competition import Competition

CompetitionIn_Pydantic = pydantic_model_creator(
    Competition, exclude_readonly=True)
Competition_Pydantic = pydantic_model_creator(Competition)
