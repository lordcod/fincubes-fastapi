from tortoise import fields

from app.models.base import TimestampedModel
from app.models.user.user import User
from app.shared.enums.enums import UserRoleEnum


class UserRole(TimestampedModel):
    id = fields.IntField(primary_key=True)
    role_type = fields.CharEnumField(enum_type=UserRoleEnum)
    profile_id = fields.IntField()
    user: User = fields.ForeignKeyField("models.User", related_name="roles")
