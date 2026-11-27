from uuid import uuid4

from tortoise import fields

from app.models.base import TimestampedModel


class ProtocolImport(TimestampedModel):
    id = fields.UUIDField(primary_key=True, default=uuid4)
    competition = fields.ForeignKeyField("models.Competition", on_delete=fields.CASCADE, null=True)
    stage = fields.CharField(max_length=20, default="prepare")
    payload = fields.JSONField()
    state = fields.JSONField()

    class Meta:
        table = "protocol_imports"
