import re
import datetime
from typing import Any, Optional
from pydantic_core import core_schema
from pydantic import GetCoreSchemaHandler
from tortoise import fields


class FlexibleTime(datetime.time):
    time_regex = re.compile(r'((\d+):)?((\d+):)?(\d{1,2})[.,](\d{1,2})')

    @classmethod
    def validate(cls, value: Any) -> 'FlexibleTime':
        if not value and isinstance(value, (bool, int, str)):
            return cls()

        if isinstance(value, FlexibleTime):
            return value

        if isinstance(value, datetime.timedelta):
            total_seconds = int(value.total_seconds())
            minutes, seconds = divmod(total_seconds, 60)
            hundredths = round(value.microseconds / 10000)
            return cls(hour=0, minute=minutes, second=seconds, microsecond=hundredths * 10000)

        if isinstance(value, datetime.time):
            return cls(hour=value.hour, minute=value.minute, second=value.second, microsecond=value.microsecond)

        if not isinstance(value, str):
            raise TypeError(
                f"Unsupported type for FlexibleTime: {type(value)}")

        match = cls.time_regex.match(value.strip().replace(',', '.'))
        if not match:
            raise ValueError(f"Invalid time format: {value}")

        minutes, seconds, hundredths = match.groups()
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0
        hundredths = int(hundredths) if hundredths else 0

        return cls(hour=0, minute=minutes, second=seconds, microsecond=hundredths*10_000)

    def __str__(self) -> str:
        if self.hour:
            return f"{self.hour}:{self.minute:02}:{self.second:02}.{int(self.microsecond / 10000):02}"
        return f"{self.minute:02}:{self.second:02}.{int(self.microsecond / 10000):02}"

    def __repr__(self) -> str:
        return f'"{self}"'  # For JSON encoding

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: GetCoreSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            python_schema=core_schema.no_info_plain_validator_function(
                cls.validate),
            json_schema=core_schema.no_info_plain_validator_function(
                cls.validate),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: str(v)),
        )


class FlexibleTimeField(fields.TimeField):
    def to_python_value(self, value: Optional[datetime.time]) -> Optional[FlexibleTime]:
        if value is None:
            return None
        return FlexibleTime.validate(value)

    def to_db_value(self, value: Optional[FlexibleTime]) -> Optional[datetime.time]:
        if value is None:
            return None
        if isinstance(value, datetime.time):
            return FlexibleTime.validate(value)
        raise ValueError(f"Unsupported value for FlexibleTimeField: {value}")
