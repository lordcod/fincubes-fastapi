from typing import TYPE_CHECKING
from tortoise import fields
from tortoise.models import Model
import uuid

if TYPE_CHECKING:
    from app.models.tokens.refresh_tokens import RefreshToken


class Session(Model):
    id = fields.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)
    revoked_at = fields.DatetimeField(null=True)

    refresh_tokens: fields.ReverseRelation

    class Meta:
        table = "sessions"
