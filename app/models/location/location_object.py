from tortoise import fields
import uuid

from app.models.base import TimestampedModel


class LocationObject(TimestampedModel):
    """One normalized club/city/region object."""

    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)

    club = fields.CharField(max_length=512, null=True)
    city = fields.CharField(max_length=255, null=True)
    region = fields.CharField(max_length=255)

    class Meta:
        table = "location_objects"
