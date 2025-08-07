from tortoise import fields
from app.models.base import TimestampedModel


class Bot(TimestampedModel):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100, unique=True)
    owner = fields.ForeignKeyField("models.User", related_name="bots")
    scopes = fields.JSONField(default=[])
    is_active = fields.BooleanField(default=True)

    def __str__(self):
        return f"Bot(id={self.id}, name='{self.name}')"
