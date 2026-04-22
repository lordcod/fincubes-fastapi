from tortoise import fields

from app.models.athlete.athlete import Athlete
from app.models.base import TimestampedModel
from app.models.review.review_item import ReviewItem
from app.models.user.user import User
from app.shared.enums.enums import ReviewDecisionActionEnum


class ReviewDecision(TimestampedModel):
    id = fields.IntField(primary_key=True)
    review_item: ReviewItem = fields.ForeignKeyField(
        "models.ReviewItem",
        related_name="decisions",
        on_delete=fields.CASCADE,
    )
    action = fields.CharEnumField(enum_type=ReviewDecisionActionEnum)
    candidate_athlete: Athlete = fields.ForeignKeyField(
        "models.Athlete",
        related_name="candidate_review_decisions",
        null=True,
        on_delete=fields.SET_NULL,
    )
    patch_payload = fields.JSONField(null=True)
    created_athlete: Athlete = fields.ForeignKeyField(
        "models.Athlete",
        related_name="created_review_decisions",
        null=True,
        on_delete=fields.SET_NULL,
    )
    result_payload = fields.JSONField(null=True)
    created_by: User = fields.ForeignKeyField(
        "models.User",
        related_name="review_decisions",
        null=True,
        on_delete=fields.SET_NULL,
    )

    class Meta:
        table = "review_decision"
