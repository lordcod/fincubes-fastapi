from tortoise import fields

from app.models.base import TimestampedModel
from app.models.user.user import User
from app.shared.enums.enums import ReviewSessionStatusEnum, ReviewSourceTypeEnum


class ReviewSession(TimestampedModel):
    id = fields.IntField(primary_key=True)
    status = fields.CharEnumField(
        enum_type=ReviewSessionStatusEnum,
        default=ReviewSessionStatusEnum.NEW,
    )
    source_type = fields.CharEnumField(enum_type=ReviewSourceTypeEnum)
    source_ref = fields.CharField(max_length=255)
    meta = fields.JSONField(default=dict)
    created_by: User = fields.ForeignKeyField(
        "models.User",
        related_name="review_sessions",
        null=True,
        on_delete=fields.SET_NULL,
    )

    class Meta:
        table = "review_session"
