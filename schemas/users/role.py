from tortoise.contrib.pydantic import pydantic_model_creator
from models.models import UserRole


UserRoleIn = pydantic_model_creator(UserRole, exclude_readonly=True)
UserRoleOut = pydantic_model_creator(UserRole)
