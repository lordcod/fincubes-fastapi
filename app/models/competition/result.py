from tortoise import fields

from app.models.athlete.athlete import Athlete
from app.models.base import TimestampedModel
from app.models.competition.competition import Competition
from app.shared.utils.flexible_time import FlexibleTimeField, ReadOnlyFlexibleTimeField


class Result(TimestampedModel):
    id = fields.IntField(primary_key=True)
    athlete: Athlete = fields.ForeignKeyField(
        "models.Athlete", related_name="results")
    competition: Competition = fields.ForeignKeyField(
        "models.Competition", related_name="results"
    )
    stroke = fields.CharField(max_length=50)
    distance = fields.IntField()
    result = FlexibleTimeField(max_length=20, null=True)
    final = FlexibleTimeField(max_length=1020, null=True)
    resolved_time = ReadOnlyFlexibleTimeField(null=True, generated=True)
    place = fields.CharField(max_length=50, null=True)
    final_rank = fields.CharField(max_length=50, null=True)
    points = fields.CharField(max_length=50, null=True)
    record = fields.CharField(max_length=255, null=True)
    dsq_final = fields.BooleanField(default=False)
    dsq = fields.BooleanField(default=False)

    class Meta:
        table = "results"
