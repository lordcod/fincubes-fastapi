from tortoise import fields

from app.models.base import TimestampedModel


class Athlete(TimestampedModel):
    id = fields.IntField(primary_key=True)
    last_name = fields.CharField(max_length=100)
    first_name = fields.CharField(max_length=100)
    birth_year = fields.CharField(max_length=4)
    club = fields.CharField(max_length=255, null=True)
    city = fields.CharField(max_length=255, null=True)
    license = fields.CharField(max_length=50, null=True)
    gender = fields.CharField(max_length=1)

    avatar_url = fields.CharField(max_length=250, null=True)
    is_top = fields.BooleanField(default=False)

    class Meta:
        table = "athletes"
