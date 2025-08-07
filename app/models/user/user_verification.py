from tortoise import fields

from app.models.base import TimestampedModel
from app.models.user.user import User
from app.shared.enums.enums import VerificationTokenEnum


class UserVerification(TimestampedModel):
    id = fields.IntField(primary_key=True)
    user: User = fields.ForeignKeyField(
        "models.User", related_name="verifications")
    attempt = fields.IntField(default=0)
    is_active = fields.BooleanField(default=True)
    token = fields.CharField(max_length=256)
    token_expiry = fields.DatetimeField()
    token_type = fields.CharEnumField(
        enum_type=VerificationTokenEnum,
        default=VerificationTokenEnum.VERIFY_EMAIL)
