from typing_extensions import Annotated
from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any, Union
from tortoise.contrib.pydantic.creator import pydantic_model_creator
from app.models.user.group import Group, GroupCollection

Group_Pydantic = pydantic_model_creator(Group)
GroupIn_Pydantic = pydantic_model_creator(
    Group, exclude_readonly=True)


GroupCollection_Pydantic = pydantic_model_creator(GroupCollection)
GroupCollectionIn_Pydantic = pydantic_model_creator(
    GroupCollection, exclude_readonly=True)


class BaseCommand(BaseModel):
    type: Literal["create", "update", "delete"]


class UserCommandPayload(BaseModel):
    id: int
    scopes: List


class UserCommand(BaseCommand):
    model: Literal["users"]
    payload: UserCommandPayload


class GroupCommand(BaseCommand):
    model: Literal["groups"]
    payload: Dict[str, Any]


class TrackCommand(BaseCommand):
    model: Literal["tracks"]
    payload: Dict[str, Any]


LuckPermCommand = Annotated[
    Union[UserCommand, GroupCommand, TrackCommand],
    Field(discriminator="model"),
]
