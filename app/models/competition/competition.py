from tortoise import fields

from app.models.base import TimestampedModel


class Competition(TimestampedModel):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    date = fields.CharField(max_length=50)
    location = fields.CharField(max_length=255)
    city = fields.CharField(max_length=255, null=True)
    organizer = fields.CharField(max_length=100)
    status = fields.CharField(max_length=100, null=True)
    links = fields.JSONField()
    start_date = fields.DateField()
    end_date = fields.DateField()

    class Meta:
        table = "competitions"
