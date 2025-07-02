from tortoise import fields

from app.models.base import TimestampedModel
from app.shared.utils.flexible_time import FlexibleTimeField


class StandardCategory(TimestampedModel):
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=10)
    stroke = fields.CharField(max_length=10)
    distance = fields.IntField()
    gender = fields.CharField(max_length=1)
    type = fields.CharField(max_length=10)
    result = FlexibleTimeField(max_length=20, null=True)
    is_active = fields.BooleanField(default=True)
