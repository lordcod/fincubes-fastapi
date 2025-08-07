from tortoise import fields, models


class Group(models.Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    display_name = fields.CharField(max_length=100)
    weight = fields.IntField()
    permissions = fields.JSONField()

    parents = fields.ManyToManyField(
        "models.Group",
        related_name="children",
        through="group_parents",
        forward_key="child_id",
        backward_key="parent_id"
    )


class GroupCollection(models.Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    groups = fields.ManyToManyField(
        "models.Group",
        related_name="collections",
        through="group_collection_groups"
    )
