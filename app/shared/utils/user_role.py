from fastapi import Depends

from app.core.errors import APIError, ErrorCode
from app.core.security.deps.user_auth import UserAuthSecurity
from app.core.security.schema import TokenType
from app.models.athlete.athlete import Athlete
from app.models.roles.coach import Coach
from app.models.roles.parent import Parent
from app.models.user.user import User
from app.models.user.user_role import UserRole
from app.shared.enums.enums import UserRoleEnum

model_map = {
    UserRoleEnum.ATHLETE: Athlete,
    UserRoleEnum.COACH: Coach,
    UserRoleEnum.PARENT: Parent,
}


async def get_profile(
    user: User, expected_role: UserRoleEnum, required_verification: bool = True
):
    if not user.verified and required_verification:
        raise APIError(ErrorCode.VERIFICATION_FAILED)

    role = await UserRole.filter(user=user).first()
    if not role or role.role_type != expected_role:
        raise APIError(ErrorCode.INVALID_ROLE)

    model = model_map[role.role_type]
    return await model.get(id=role.profile_id)


def get_role(expected_role: UserRoleEnum, required_verification: bool = True):
    async def wrapped(user: User = Depends(UserAuthSecurity())):
        return await get_profile(user, expected_role, required_verification)

    return wrapped
