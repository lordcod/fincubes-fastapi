from tortoise import fields

from app.models.base import TimestampedModel


class LocationObject(TimestampedModel):
    """One normalized club/city/region object with all observed aliases."""

    id = fields.UUIDField(primary_key=True)
    aliases = fields.JSONField(default=list)

    club = fields.CharField(max_length=512, null=True)
    club_id = fields.UUIDField(null=True)
    city = fields.CharField(max_length=255, null=True)
    city_id = fields.UUIDField(null=True)
    region = fields.CharField(max_length=255)
    region_id = fields.UUIDField()

    required = fields.JSONField(default=list)

    class Meta:
        table = "location_objects"
