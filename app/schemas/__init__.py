import datetime
from typing import TYPE_CHECKING, Type, TypeVar, Union, cast

from pydantic import BaseModel
from tortoise.contrib.pydantic import PydanticModel, pydantic_model_creator

T = TypeVar("T")


def _with_nested(base_model: Union[type[PydanticModel], type[BaseModel]], **nested_fields) -> type[PydanticModel]:
    annotations = {}
    namespace = {"__module__": base_model.__module__}

    for name, value in nested_fields.items():
        if isinstance(value, tuple) and len(value) == 2:
            annotations[name] = value[0]
            namespace[name] = value[1]
        else:
            annotations[name] = value
    namespace["__annotations__"] = annotations

    return type(f"{base_model.__name__}WithNested", (base_model,), namespace)


def _create_pydantic_model(model, **kwargs):
    custom_encoders = {
        datetime.time: lambda v: str(v),
    }

    model_config = kwargs.get("model_config") or {}

    existing_encoders = model_config.get("json_encoders", {})

    merged_encoders = {**existing_encoders, **custom_encoders}
    model_config["json_encoders"] = merged_encoders
    kwargs["model_config"] = model_config

    return pydantic_model_creator(model, **kwargs)


if TYPE_CHECKING:
    def with_nested(
        base_model: T,
        **nested_fields
    ) -> T:
        return base_model
    create_pydantic_model = pydantic_model_creator
else:
    create_pydantic_model = _create_pydantic_model
    with_nested = _with_nested
