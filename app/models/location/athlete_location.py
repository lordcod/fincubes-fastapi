from tortoise import fields

from app.models.base import TimestampedModel


class AthleteLocation(TimestampedModel):
    """A catalog location linked to an athlete by the observed source alias."""

    id = fields.IntField(primary_key=True)
    alias = fields.CharField(max_length=512)

    athlete = fields.ForeignKeyField(
        "models.Athlete",
        related_name="location_links",
        on_delete=fields.CASCADE,
    )
    location_object = fields.ForeignKeyField(
        "models.LocationObject",
        related_name="athlete_links",
        on_delete=fields.RESTRICT,
    )

    class Meta:
        table = "locations"
        unique_together = (("athlete", "location_object", "alias"),)
