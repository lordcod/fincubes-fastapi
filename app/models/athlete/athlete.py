from tortoise import fields

from app.models.base import TimestampedModel


class Athlete(TimestampedModel):
    id = fields.IntField(primary_key=True)
    last_name = fields.CharField(max_length=100)
    first_name = fields.CharField(max_length=100)
    birth_year = fields.CharField(max_length=4)
    location_object = fields.ForeignKeyField(
        "models.LocationObject",
        related_name="athletes",
        null=True,
        on_delete=fields.SET_NULL,
    )
    license = fields.CharField(max_length=50, null=True)
    gender = fields.CharField(max_length=1)

    avatar_url = fields.CharField(max_length=250, null=True)
    is_top = fields.BooleanField(default=False)

    @property
    def club(self):
        location = getattr(self, "location_object", None)
        return location.club if location else None

    @property
    def city(self):
        location = getattr(self, "location_object", None)
        return location.city if location else None

    @property
    def region(self):
        location = getattr(self, "location_object", None)
        return location.region if location else None

    class Meta:
        table = "athletes"
