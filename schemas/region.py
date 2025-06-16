from tortoise.contrib.pydantic import pydantic_model_creator

from models.models import Region
from schemas import create_pydantic_model

RegionIn = pydantic_model_creator(Region, exclude_readonly=True)
RegionOut = create_pydantic_model(Region)
