from tortoise import fields

from app.models.base import TimestampedModel


class User(TimestampedModel):
    id = fields.IntField(primary_key=True)
    email = fields.CharField(max_length=255, unique=True)
    hashed_password = fields.CharField(max_length=255)
    verified = fields.BooleanField(default=False)
    permissions = fields.JSONField(default=[])
