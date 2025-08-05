from tortoise import fields

from app.models.athlete.athlete import Athlete
from app.models.base import TimestampedModel
from app.models.roles.coach import Coach


class CoachAthlete(TimestampedModel):
    id = fields.IntField(primary_key=True)
    status = fields.CharField(max_length=50, default="active")
    coach: Coach = fields.ForeignKeyField(
        "models.Coach", related_name="coach_athletes")
    athlete: Athlete = fields.ForeignKeyField(
        "models.Athlete", related_name="athlete_coaches")
