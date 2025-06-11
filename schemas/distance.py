from pydantic import BaseModel
from models.models import Distance
from tortoise.contrib.pydantic import pydantic_model_creator

from schemas import with_nested
from schemas.competition import Competition_Pydantic


DistanceIn_Pydantic = pydantic_model_creator(Distance, exclude_readonly=True)
Distance_Pydantic = with_nested(
    pydantic_model_creator(Distance), competition=Competition_Pydantic
)


class DistanceOrderUpdate_Pydantic(BaseModel):
    id: int
    order: int

    class Config:
        from_attributes = True
