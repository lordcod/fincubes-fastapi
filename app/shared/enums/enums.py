from enum import StrEnum


class UserRoleEnum(StrEnum):
    ATHLETE = "ATHLETE"
    COACH = "COACH"
    PARENT = "PARENT"
    ADMIN = "ADMIN"
    ORGANIZER = "ORGANIZER"


class VerificationTokenEnum(StrEnum):
    RESET_PASSWORD = "RESET_PASSWORD"
    VERIFY_EMAIL = "VERIFY_EMAIL"
