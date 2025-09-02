from tortoise import fields
from tortoise.models import Model
import uuid

from app.models.tokens.sessions import Session


class RefreshToken(Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    session: fields.ForeignKeyRelation[Session] = fields.ForeignKeyField(
        "models.Session",
        related_name="refresh_tokens",
    )
    access_id = fields.UUIDField(null=True)
    issued_at = fields.DatetimeField()
    expires_at = fields.DatetimeField()
    revoked_at = fields.DatetimeField(null=True)
    grace_until = fields.DatetimeField(null=True)
    request_info = fields.JSONField(null=True)

    class Meta:
        table = "refresh_tokens"
