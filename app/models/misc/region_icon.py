from tortoise import fields

from app.models.base import TimestampedModel


class RegionIcon(TimestampedModel):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, unique=True)
    format = fields.CharField(max_length=16)
    icon_url = fields.CharField(max_length=512)

    class Meta:
        table = "region_icons"
