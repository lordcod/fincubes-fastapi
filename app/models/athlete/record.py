from tortoise import fields

from app.models.base import TimestampedModel


class Record(TimestampedModel):
    id = fields.IntField(pk=True)
    stroke = fields.CharField(max_length=50)
    distance = fields.IntField()
    time = fields.CharField(max_length=20)
    firstname = fields.CharField(max_length=100)
    lastname = fields.CharField(max_length=100)
    birth_year = fields.IntField()
    region = fields.CharField(max_length=100)
    date = fields.DateField()
    city = fields.CharField(max_length=100)
    country = fields.CharField(max_length=100, null=True)
    event_name = fields.CharField(max_length=100)
    gender = fields.CharField(max_length=1, null=True)
    category = fields.CharField(max_length=5, null=True)
    is_active = fields.BooleanField(default=True)

    class Meta:
        table = "records"
