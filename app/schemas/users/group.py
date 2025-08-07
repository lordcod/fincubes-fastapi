from typing import List
from tortoise.contrib.pydantic.creator import pydantic_model_creator
from app.models.user.group import Group, GroupCollection
from app.schemas import with_nested

GroupDepth0 = pydantic_model_creator(Group)
Group_Pydantic = with_nested(GroupDepth0, parents=List[GroupDepth0])
GroupIn_Pydantic = with_nested(pydantic_model_creator(
    Group, exclude_readonly=True), parents=List[int])


GroupCollection_Pydantic = with_nested(
    pydantic_model_creator(GroupCollection), groups=List[GroupDepth0])
GroupCollectionIn_Pydantic = pydantic_model_creator(
    GroupCollection, exclude_readonly=True)
