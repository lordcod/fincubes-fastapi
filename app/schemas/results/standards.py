
from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.misc.standard_category import StandardCategory
from app.schemas import create_pydantic_model

StandardIn = pydantic_model_creator(StandardCategory, exclude_readonly=True)
StandardOut = create_pydantic_model(StandardCategory)
