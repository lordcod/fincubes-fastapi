from tortoise.contrib.pydantic import pydantic_model_creator
from models.models import Athlete, Coach
from schemas import with_nested


BaseCoachIn = pydantic_model_creator(Coach, exclude_readonly=True)


class CoachIn(BaseCoachIn):
    model_config = {
        **BaseCoachIn.model_config,
        "extra": "ignore"
    }


CoachOut = pydantic_model_creator(Coach)


class CoachOutWithStatus(CoachOut):
    status: str
