from typing import List,  Optional
from pydantic import BaseModel
from models.flexible_time import FlexibleTime
from models.models import Competition, Result
from tortoise.contrib.pydantic import pydantic_model_creator

# Models

CompetitionIn_Pydantic = pydantic_model_creator(
    Competition, exclude_readonly=True)
Competition_Pydantic = pydantic_model_creator(Competition)
