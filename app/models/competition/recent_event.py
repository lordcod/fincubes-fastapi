from tortoise import fields
from tortoise.models import Model

from app.models.base import TimestampedModel
from app.models.competition.competition import Competition


class RecentEvent(TimestampedModel):
    id = fields.IntField(pk=True)
    competition: Competition = fields.ForeignKeyField(
        "models.Competition", related_name="recent_mentions"
    )

    class Meta:
        table = "recent_events"
