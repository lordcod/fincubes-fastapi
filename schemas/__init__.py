import datetime
from typing import TYPE_CHECKING
from tortoise.contrib.pydantic import pydantic_model_creator, PydanticModel
from typing import TypeVar
T = TypeVar('T')


def with_nested(base_model, **nested_fields) -> PydanticModel:
    annotations = {}
    namespace = {"__module__": base_model.__module__}

    for name, value in nested_fields.items():
        if isinstance(value, tuple) and len(value) == 2:
            # формат: поле = (тип, значение_по_умолчанию)
            annotations[name] = value[0]
            namespace[name] = value[1]
        else:
            annotations[name] = value
            # не задаём значение по умолчанию
    namespace["__annotations__"] = annotations

    return type(
        f"{base_model.__name__}WithNested",
        (base_model,),
        namespace
    )


if TYPE_CHECKING:
    create_pydantic_model = pydantic_model_creator
else:
    def create_pydantic_model(model, **kwargs):
        custom_encoders = {
            datetime.time: lambda v: str(v),
        }

        model_config = kwargs.get("model_config") or {}

        existing_encoders = model_config.get("json_encoders", {})

        merged_encoders = {**existing_encoders, **custom_encoders}
        model_config["json_encoders"] = merged_encoders
        kwargs["model_config"] = model_config

        return pydantic_model_creator(model, **kwargs)
