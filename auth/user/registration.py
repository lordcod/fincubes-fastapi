from typing import Optional

from tortoise.transactions import in_transaction

from misc.errors import APIError, ErrorCode
from misc.security import hash_password
from models.enums import UserRoleEnum
from models.models import Athlete, Coach, Parent, User, UserRole
from schemas.auth import UserCreate


class UserRegistration:
    def __init__(self, data: UserCreate):
        self.data = data
        self.user: Optional[User] = None

    async def register_user(self):
        async with in_transaction() as connection:
            await self._validate()
            await self._create_user(connection)
            await self._assign_role(connection)
        return self.user

    async def _validate(self):
        existing_user = await User.filter(email=self.data.email).first()
        if existing_user:
            raise APIError(ErrorCode.EMAIL_ALREADY_TAKEN)

    async def _create_user(self, connection):
        hashed_password = hash_password(self.data.password)
        self.user = await User.create(
            email=self.data.email,
            hashed_password=hashed_password,
            using_db=connection
        )

    async def _assign_role(self, connection):
        pass


class AthleteRegistration(UserRegistration):
    async def _assign_role(self, connection):
        athlete_id = self.data.metadata.get("id")
        athlete = await Athlete.get_or_none(id=athlete_id)

        if not athlete:
            raise APIError(ErrorCode.ATHLETE_NOT_FOUND)

        if await UserRole.filter(
            role_type=UserRoleEnum.ATHLETE,
            profile_id=athlete.id
        ).exists():
            raise APIError(ErrorCode.ATHLETE_ALREADY_BOUND_TO_OTHER_USER)

        await UserRole.create(
            user=self.user,
            role_type=UserRoleEnum.ATHLETE,
            profile_id=athlete.id,
            using_db=connection
        )


class CoachRegistration(UserRegistration):
    async def _assign_role(self, connection):
        coach = await Coach.create(
            first_name=self.data.metadata.get("first_name"),
            last_name=self.data.metadata.get("last_name"),
            middle_name=self.data.metadata.get("middle_name"),
            club=self.data.metadata.get("club"),
            city=self.data.metadata.get("city"),
            using_db=connection
        )

        await UserRole.create(
            user=self.user,
            role_type=UserRoleEnum.COACH,
            profile_id=coach.id,
            using_db=connection
        )


class ParentRegistration(UserRegistration):
    async def _assign_role(self, connection):
        parent = await Parent.create(using_db=connection)
        await UserRole.create(
            user=self.user,
            role_type=UserRoleEnum.PARENT,
            profile_id=parent.id,
            using_db=connection
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
