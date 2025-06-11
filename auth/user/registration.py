from typing import Optional

from misc.errors import APIError, ErrorCode
from misc.security import hash_password
from models.models import Athlete, Coach, Parent, User, UserRole
from models.enums import UserRoleEnum
from schemas.auth import UserCreate


class UserRegistration:
    def __init__(self, data: UserCreate):
        self.data = data
        self.user: Optional[User] = None

    async def register_user(self):
        await self._validate()
        await self._create_user()
        await self._assign_role()
        return self.user

    async def _validate(self):
        existing_user = await User.filter(email=self.data.email).first()
        if existing_user:
            raise APIError(ErrorCode.EMAIL_ALREADY_TAKEN)

    async def _create_user(self):
        hashed_password = hash_password(self.data.password)
        self.user = await User.create(
            email=self.data.email, hashed_password=hashed_password
        )

    async def _assign_role(self):
        pass


class AthleteRegistration(UserRegistration):
    async def _assign_role(self):
        athlete_id = self.data.metadata.get("id")
        athlete = await Athlete.get_or_none(id=athlete_id)

        if not athlete:
            raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

        if await UserRole.filter(
            role_type=UserRoleEnum.ATHLETE, profile_id=athlete.id
        ).exists():
            raise APIError(ErrorCode.ATHLETE_ALREADY_BOUND_TO_OTHER_USER)

        await UserRole.create(
            user=self.user, role_type=UserRoleEnum.ATHLETE, profile_id=athlete.id
        )


class CoachRegistration(UserRegistration):
    async def _assign_role(self):
        coach = await Coach.create(
            first_name=self.data.metadata.get("first_name"),
            last_name=self.data.metadata.get("last_name"),
            middle_name=self.data.metadata.get("middle_name"),
            club=self.data.metadata.get("club"),
            city=self.data.metadata.get("city"),
        )

        await UserRole.create(
            user=self.user, role_type=UserRoleEnum.COACH, profile_id=coach.id
        )


class ParentRegistration(UserRegistration):
    async def _assign_role(self):
        parent = await Parent.create()
        await UserRole.create(
            user=self.user, role_type=UserRoleEnum.PARENT, profile_id=parent.id
        )


def get_registration_handler(data: UserCreate) -> UserRegistration:
    match data.role:
        case None:
            return UserRegistration(data)
        case "athlete":
            return AthleteRegistration(data)
        case "coach":
            return CoachRegistration(data)
        case "parent":
            return ParentRegistration(data)
        case _:
            raise APIError(ErrorCode.INVALID_USER_ROLE)
