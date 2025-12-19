from tortoise import fields

from app.models.athlete.athlete import Athlete
from app.models.base import TimestampedModel
from app.models.competition.competition import Competition
from app.shared.utils.flexible_time import FlexibleTimeField, ReadOnlyFlexibleTimeField


class CompetitionResult(TimestampedModel):
    id = fields.BigIntField(pk=True)  # сохраняем старый ID
    stroke = fields.TextField()
    distance = fields.IntField()
    points = fields.TextField(null=True)
    record = fields.TextField(null=True)
    athlete: fields.ForeignKeyRelation[Athlete] = fields.ForeignKeyField(
        "models.Athlete", related_name="results")
    competition: fields.ForeignKeyRelation[Competition] = fields.ForeignKeyField(
        "models.Competition", related_name="results"
    )
    resolved_time = ReadOnlyFlexibleTimeField(null=True)

    stages: fields.ReverseRelation["CompetitionStage"]

    class Meta:
        table = "competition_results"  # имя таблицы в базе


class CompetitionStage(TimestampedModel):
    id = fields.BigIntField(pk=True)
    result: fields.ForeignKeyRelation[CompetitionResult] = fields.ForeignKeyField(
        "models.CompetitionResult",
        related_name="stages",
        on_delete=fields.CASCADE
    )
    kind = fields.TextField()  # RESULT, HEAT, SEMIFINAL, FINAL
    order = fields.IntField()
    time = FlexibleTimeField(null=True)
    status = fields.TextField()
    place = fields.TextField(null=True)
    rank = fields.TextField(null=True)
    is_final = fields.BooleanField(default=False)

    class Meta:
        table = "competition_stages"
