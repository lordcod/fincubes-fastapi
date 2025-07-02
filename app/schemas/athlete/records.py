
from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.athlete.record import Record

RecordIn = pydantic_model_creator(Record, exclude_readonly=True)
RecordOut = pydantic_model_creator(Record)
