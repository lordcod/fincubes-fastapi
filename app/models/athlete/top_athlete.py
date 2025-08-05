from tortoise import fields

from app.models.athlete.athlete import Athlete
from app.models.base import TimestampedModel


class TopAthlete(TimestampedModel):
    id = fields.IntField(primary_key=True)
    athlete: Athlete = fields.ForeignKeyField(
        "models.Athlete", related_name="top_mentions")

    class Meta:
        table = "top_athletes"
