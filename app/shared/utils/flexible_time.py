import datetime
import re
from typing import Any, Optional

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema
from tortoise import fields


class FlexibleTime(datetime.time):
    time_regex = re.compile(
        r"^(?:(?P<minutes>\d{1,2}):)?(?P<seconds>\d{1,2})[.,](?P<hundredths>\d{1,2})$"
    )

    @classmethod
    def validate(cls, value: Any) -> "FlexibleTime":
        if not value and isinstance(value, (bool, int, str)):
            return cls()

        if isinstance(value, FlexibleTime):
            return value

        if isinstance(value, datetime.timedelta):
            total_seconds = int(value.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            hundredths = round(value.microseconds / 10000)
            return cls(
                hour=0, minute=minutes, second=seconds, microsecond=hundredths * 10000
            )

        if isinstance(value, datetime.time):
            return cls(
                hour=value.hour,
                minute=value.minute,
                second=value.second,
                microsecond=value.microsecond,
            )

        if not isinstance(value, str):
            raise TypeError(
                f"Unsupported type for FlexibleTime: {type(value)}")

        match = cls.time_regex.match(value.strip().replace(",", "."))
        if not match:
            raise ValueError(f"Invalid time format: {value}")

        groups = match.groupdict()
        minutes = int(groups.get("minutes") or 0)
        seconds = int(groups.get("seconds") or 0)
        hundredths = int(groups.get("hundredths") or 0)

        return cls(
            hour=0, minute=minutes, second=seconds, microsecond=hundredths * 10_000
        )

    def __str__(self) -> str:
        if self.hour:
            return f"{self.hour}:{self.minute:02}:{self.second:02},{int(self.microsecond / 10000):02}"
        return f"{self.minute:02}:{self.second:02},{int(self.microsecond / 10000):02}"

    def __repr__(self) -> str:
        return f'"{self}"'

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler: GetCoreSchemaHandler
    ) -> dict:
        return {
            "type": "string",
            "title": "FlexibleTime",
            "description": "Формат времени: mm:ss.SS или ss.SS",
            "examples": ["01:23.45", "56.78"],
        }

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            python_schema=core_schema.no_info_plain_validator_function(
                cls.validate),
            json_schema=core_schema.no_info_plain_validator_function(
                cls.validate),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v)
            ),
        )


class FlexibleTimeField(fields.Field[FlexibleTime], FlexibleTime):
    def to_python_value(self, value: Optional[datetime.time]) -> Optional[FlexibleTime]:
        if value is None:
            return None
        return FlexibleTime.validate(value)

    def to_db_value(self, value, instance):
        if value is None:
            return None

        if isinstance(value, FlexibleTime):
            return datetime.time(
                hour=value.hour,
                minute=value.minute,
                second=value.second,
                microsecond=value.microsecond,
                tzinfo=datetime.timezone.utc,
            )

        if isinstance(value, datetime.time):
            if value.tzinfo is None:
                return value.replace(tzinfo=datetime.timezone.utc)
            return value

        raise ValueError(f"Unsupported value for FlexibleTimeField: {value}")

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return FlexibleTime.__get_pydantic_core_schema__(source_type, handler)

    skip_to_python_if_native = True
    SQL_TYPE = "TIME"

    class _db_oracle:
        SQL_TYPE = "NVARCHAR2(8)"

    class _db_mysql:
        SQL_TYPE = "TIME(6)"

    class _db_postgres:
        SQL_TYPE = "TIMETZ"


class ReadOnlyFlexibleTimeField(FlexibleTimeField):
    def to_db_value(self, value, instance):
        raise RuntimeError("Field is read-only")
