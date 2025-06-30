from tortoise import fields

from app.models.base import TimestampedModel


class Region(TimestampedModel):
    id = fields.IntField(pk=True)
    region = fields.CharField(max_length=255)
    organization = fields.CharField(max_length=512)
    president = fields.CharField(max_length=255)
    emails = fields.JSONField()
    phones = fields.JSONField()
    socials = fields.JSONField()
    rating = fields.FloatField()
