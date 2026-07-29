from tortoise import fields

from app.models.athlete.athlete import Athlete
from app.models.base import TimestampedModel
from app.models.competition.relay_result import RelayResult
from app.shared.utils.flexible_time import FlexibleTimeField


class RelayLeg(TimestampedModel):
    id = fields.IntField(primary_key=True)
    relay_result: RelayResult = fields.ForeignKeyField(
        "models.RelayResult",
        related_name="legs",
        on_delete=fields.CASCADE,
    )
    athlete: Athlete = fields.ForeignKeyField(
        "models.Athlete",
        related_name="relay_legs",
        on_delete=fields.RESTRICT,
    )
    order = fields.IntField()
    result = FlexibleTimeField(max_length=20, null=True)
    metadata = fields.JSONField(null=True)

    def validate_order(self) -> None:
        if self.order <= 0:
            raise ValueError("RelayLeg.order must be greater than 0")

    async def save(self, *args, **kwargs):
        self.validate_order()
        return await super().save(*args, **kwargs)

    class Meta:
        table = "relay_legs"
        unique_together = (("relay_result", "order"),)
