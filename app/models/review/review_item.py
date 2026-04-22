from tortoise import fields

from app.models.athlete.athlete import Athlete
from app.models.base import TimestampedModel
from app.models.review.review_session import ReviewSession
from app.shared.enums.enums import ReviewConfidenceEnum, ReviewItemStatusEnum


class ReviewItem(TimestampedModel):
    id = fields.IntField(primary_key=True)
    session: ReviewSession = fields.ForeignKeyField(
        "models.ReviewSession",
        related_name="items",
        on_delete=fields.CASCADE,
    )
    external_id = fields.CharField(max_length=255)
    status = fields.CharEnumField(
        enum_type=ReviewItemStatusEnum,
        default=ReviewItemStatusEnum.NEW,
    )
    source_payload = fields.JSONField()
    source_city = fields.CharField(max_length=255, null=True)
    candidates_snapshot = fields.JSONField(default=list)
    candidate_count = fields.IntField(default=0)
    selected_athlete: Athlete = fields.ForeignKeyField(
        "models.Athlete",
        related_name="review_items",
        null=True,
        on_delete=fields.SET_NULL,
    )
    auto_match = fields.BooleanField(default=False)
    confidence = fields.CharEnumField(
        enum_type=ReviewConfidenceEnum,
        default=ReviewConfidenceEnum.LOW,
    )
    note = fields.TextField(null=True)

    class Meta:
        table = "review_item"
        unique_together = (("session_id", "external_id"),)
