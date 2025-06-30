from typing import List

from tortoise import fields
from tortoise.models import Model

from app.models.athlete.athlete import Athlete
from app.models.base import TimestampedModel


class Parent(TimestampedModel):
    id = fields.IntField(pk=True)
    athletes: List[Athlete] = fields.ManyToManyField(
        "models.Athlete", related_name="parents")

    class Meta:
        table = "parents"
