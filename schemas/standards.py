from models.models import StandardCategory
from tortoise.contrib.pydantic import pydantic_model_creator
from schemas import create_pydantic_model

StandardIn = pydantic_model_creator(StandardCategory, exclude_readonly=True)
StandardOut = create_pydantic_model(StandardCategory)
