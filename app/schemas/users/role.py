from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.user.user_role import UserRole

UserRoleIn = pydantic_model_creator(UserRole, exclude_readonly=True)
UserRoleOut = pydantic_model_creator(UserRole)
