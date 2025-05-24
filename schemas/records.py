from models.models import Record
from tortoise.contrib.pydantic import pydantic_model_creator


RecordIn = pydantic_model_creator(Record, exclude_readonly=True)
RecordOut = pydantic_model_creator(Record)
