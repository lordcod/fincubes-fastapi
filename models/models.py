from tortoise import fields
from tortoise.models import Model

from models.flexible_time import FlexibleTimeField


class TimestampedModel(Model):
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class Competition(TimestampedModel):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    date = fields.CharField(max_length=50)
    location = fields.CharField(max_length=255)
    organizer = fields.CharField(max_length=100)
    status = fields.CharField(max_length=100, null=True)
    links = fields.JSONField()
    start_date = fields.DateField()
    end_date = fields.DateField()

    class Meta:
        table = "competitions"


class Distance(TimestampedModel):
    id = fields.IntField(pk=True)
    competition: Competition = fields.ForeignKeyField(
        "models.Competition", related_name="distances")
    order = fields.IntField()
    stroke = fields.CharField(max_length=50)
    distance = fields.IntField()
    category = fields.CharField(max_length=255, null=True)
    gender = fields.CharField(max_length=1)
    min_year = fields.IntField(null=True)
    max_year = fields.IntField(null=True)

    class Meta:
        table = "distances"


class Athlete(TimestampedModel):
    id = fields.IntField(pk=True)
    last_name = fields.CharField(max_length=100)
    first_name = fields.CharField(max_length=100)
    birth_year = fields.CharField(max_length=4)
    club = fields.CharField(max_length=255)
    city = fields.CharField(max_length=255, null=True)
    license = fields.CharField(max_length=50)
    gender = fields.CharField(max_length=1)

    class Meta:
        table = "athletes"


class Result(TimestampedModel):
    id = fields.IntField(pk=True)
    athlete: Athlete = fields.ForeignKeyField(
        "models.Athlete", related_name="results")
    competition: Competition = fields.ForeignKeyField(
        "models.Competition", related_name="results")
    stroke = fields.CharField(max_length=50)
    distance = fields.IntField()
    result = FlexibleTimeField(max_length=20, null=True)
    final = FlexibleTimeField(max_length=1020, null=True)
    place = fields.CharField(max_length=50, null=True)
    final_rank = fields.CharField(max_length=50, null=True)
    points = fields.CharField(max_length=50, null=True)
    record = fields.CharField(max_length=255, null=True)
    dsq_final = fields.BooleanField(default=False)
    dsq = fields.BooleanField(default=False)

    class Meta:
        table = "results"


class TopAthlete(TimestampedModel):
    id = fields.IntField(pk=True)
    athlete = fields.ForeignKeyField(
        'models.Athlete', related_name='top_mentions')

    class Meta:
        table = "top_athletes"


class RecentEvent(TimestampedModel):
    id = fields.IntField(pk=True)
    competition = fields.ForeignKeyField(
        'models.Competition', related_name='recent_mentions')

    class Meta:
        table = "recent_events"


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


class StandardCategory(TimestampedModel):
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=10)
    stroke = fields.CharField(max_length=10)
    distance = fields.IntField()
    gender = fields.CharField(max_length=1)
    type = fields.CharField(max_length=10)
    result = FlexibleTimeField(max_length=20, null=True)
    is_active = fields.BooleanField(default=True)

# ROLES


class Coach(TimestampedModel):
    id = fields.IntField(pk=True)
    last_name = fields.CharField(max_length=100)
    first_name = fields.CharField(max_length=100)
    middle_name = fields.CharField(max_length=100)
    club = fields.CharField(max_length=255)
    city = fields.CharField(max_length=255, null=True)


class Parent(TimestampedModel):
    id = fields.IntField(pk=True)
    athletes = fields.ManyToManyField(
        'models.Athlete',
        related_name='parents'
    )

# LINKED


class CoachAthlete(TimestampedModel):
    id = fields.IntField(pk=True)
    coach = fields.ForeignKeyField(
        'models.Coach', related_name='coach_athletes')
    athlete = fields.ForeignKeyField(
        'models.Athlete', related_name='athlete_coaches')
    # pending, accepted, rejected
    status = fields.CharField(max_length=50, default='active')

# AUTH


class User(TimestampedModel):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    hashed_password = fields.CharField(max_length=255)
    role = fields.CharField(max_length=20, null=True)
    admin = fields.BooleanField(default=False)
    premium = fields.BooleanField(default=False)
    verified = fields.BooleanField(default=False)

    athlete = fields.ForeignKeyField(
        "models.Athlete",
        related_name="user",
        null=True,
        on_delete=fields.SET_NULL,
        unique=True
    )


class UserVerification(TimestampedModel):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='verifications')
    code = fields.CharField(max_length=6)
    attempt = fields.IntField(default=0)
    is_active = fields.BooleanField(default=True)


class UserAthlete(TimestampedModel):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='user_athlete')
    athlete = fields.ForeignKeyField(
        "models.Athlete",
        related_name="user_athlete"
    )


class UserParent(TimestampedModel):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='user_parent')
    parent = fields.ForeignKeyField(
        'models.Parent', related_name='user_parent')


class UserCoach(TimestampedModel):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='user_coach')
    coach = fields.ForeignKeyField('models.Coach', related_name='user_coach')
