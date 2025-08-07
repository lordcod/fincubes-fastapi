from tortoise import fields

from app.models.base import TimestampedModel
from app.models.competition.competition import Competition


class Distance(TimestampedModel):
    id = fields.IntField(primary_key=True)
    competition: Competition = fields.ForeignKeyField(
        "models.Competition", related_name="distances"
    )
    order = fields.IntField()
    stroke = fields.CharField(max_length=50)
    distance = fields.IntField()
    category = fields.CharField(max_length=255, null=True)
    gender = fields.CharField(max_length=1)
    min_year = fields.IntField(null=True)
    max_year = fields.IntField(null=True)

    class Meta:
        table = "distances"
