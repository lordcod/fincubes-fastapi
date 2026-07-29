from tortoise import fields

from app.models.base import TimestampedModel
from app.models.competition.competition import Competition
from app.shared.utils.flexible_time import FlexibleTimeField


class RelayResult(TimestampedModel):
    id = fields.IntField(primary_key=True)
    competition: Competition = fields.ForeignKeyField(
        "models.Competition",
        related_name="relay_results",
        on_delete=fields.CASCADE,
    )
    name = fields.CharField(max_length=512)
    stroke = fields.CharField(max_length=50)
    distance = fields.IntField()
    relay_count = fields.IntField(default=1)
    gender = fields.CharField(max_length=1)
    result = FlexibleTimeField(max_length=20, null=True)
    place = fields.CharField(max_length=50, null=True)
    points = fields.CharField(max_length=50, null=True)
    status = fields.CharField(max_length=20, default="COMPLETED")
    metadata = fields.JSONField(null=True)

    @property
    def total_distance(self) -> int:
        return self.distance * self.relay_count

    def validate_relay(self) -> None:
        if self.distance <= 0:
            raise ValueError("RelayResult.distance must be greater than 0")
        if self.relay_count <= 1:
            raise ValueError("RelayResult.relay_count must be greater than 1")

    async def save(self, *args, **kwargs):
        self.validate_relay()
        return await super().save(*args, **kwargs)

    class Meta:
        table = "relay_results"
