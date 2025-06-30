from tortoise import fields

from app.models.base import TimestampedModel


class Coach(TimestampedModel):
    id = fields.IntField(pk=True)
    last_name = fields.CharField(max_length=100)
    first_name = fields.CharField(max_length=100)
    middle_name = fields.CharField(max_length=100)
    club = fields.CharField(max_length=255)
    city = fields.CharField(max_length=255, null=True)
