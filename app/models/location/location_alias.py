import uuid

from tortoise import fields

from app.models.base import TimestampedModel
from app.shared.utils.location_text import normalize_location_text


class LocationAlias(TimestampedModel):
    """Protocol alias with context required to resolve a location object."""

    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    location_object = fields.ForeignKeyField(
        "models.LocationObject",
        related_name="alias_rules",
        on_delete=fields.CASCADE,
    )
    alias = fields.CharField(max_length=512)
    alias_key = fields.CharField(max_length=512)
    required = fields.JSONField(default=list)

    async def save(self, *args, **kwargs):
        self.alias = self.alias.strip()
        self.alias_key = normalize_location_text(self.alias)
        await super().save(*args, **kwargs)

    class Meta:
        table = "location_aliases"
        unique_together = (("location_object", "alias_key"),)
