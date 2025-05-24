from models.models import Coach, Parent

from tortoise.contrib.pydantic import pydantic_model_creator


RecordIn = pydantic_model_creator(Parent, exclude_readonly=True)
RecordOut = pydantic_model_creator(Parent)


RecordIn = pydantic_model_creator(Coach, exclude_readonly=True)
RecordOut = pydantic_model_creator(Coach)
