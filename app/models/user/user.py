from tortoise import fields

from app.models.base import TimestampedModel


class User(TimestampedModel):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    hashed_password = fields.CharField(max_length=255)
    admin = fields.BooleanField(default=False)
    premium = fields.BooleanField(default=False)
    verified = fields.BooleanField(default=False)
