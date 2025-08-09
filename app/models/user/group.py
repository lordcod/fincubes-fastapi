from tortoise import fields, models


class Group(models.Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    display_name = fields.CharField(max_length=100)
    weight = fields.IntField()
    permissions = fields.JSONField(default=[])
    parents = fields.JSONField(default=[])


class GroupCollection(models.Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    groups = fields.JSONField(default=[])
