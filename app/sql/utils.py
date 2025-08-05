import warnings
from tortoise.fields import (
    IntField,
    CharField,
    BooleanField,
    FloatField,
    DatetimeField,
    DateField,
    TimeField,
    UUIDField,
    TextField,
    JSONField
)
from tortoise.fields.relational import ForeignKeyFieldInstance
from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    Boolean,
    Float,
    DateTime,
    Date,
    Time,
    Text,
    MetaData,
    JSON
)
from sqlalchemy.dialects.postgresql import UUID
from app.shared.utils.flexible_time import FlexibleTimeField


TORTOISE_TO_SA_TYPE = {
    IntField: Integer,
    CharField: lambda f: String(f.max_length),
    BooleanField: Boolean,
    FloatField: Float,
    DatetimeField: DateTime,
    DateField: Date,
    TimeField: Time,
    TextField: Text,
    UUIDField: UUID,
    FlexibleTimeField: Time,
    JSONField: JSON,
}


def tortoise_model_to_sqlalchemy_table(model_cls) -> Table:
    columns = []

    for field_name, field in model_cls._meta.fields_map.items():
        if isinstance(field, ForeignKeyFieldInstance):
            field_name = f"{field_name}_id"
            col_type = Integer
        else:
            for tortoise_type, sa_type_factory in TORTOISE_TO_SA_TYPE.items():
                if isinstance(field, tortoise_type):
                    col_type = sa_type_factory if isinstance(
                        sa_type_factory, type) else sa_type_factory(field)
                    break
            else:
                warnings.warn(
                    f"Unmapped field: {field_name} ({type(field)}) in {model_cls.__name__}")
                continue

        kwargs = {}
        if field.pk:
            kwargs["primary_key"] = True
        if field.null:
            kwargs["nullable"] = True
        else:
            kwargs["nullable"] = False
        if hasattr(field, "default") and field.default is not None:
            kwargs["default"] = field.default

        col = Column(field_name, col_type, **kwargs)
        columns.append(col)
    return Table(model_cls._meta.db_table, MetaData(), *columns)
