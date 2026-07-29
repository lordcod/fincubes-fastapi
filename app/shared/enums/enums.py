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


class GenderEnum(StrEnum):
    FEMALE = "F"
    MALE = "M"
    MIXED = "X"
    ALL = "A"


class EventTypeEnum(StrEnum):
    INDIVIDUAL = "INDIVIDUAL"
    RELAY = "RELAY"


class CoachAthleteStatusEnum(StrEnum):
    ACCEPTED = 'accepted'
    PENDING = 'pending'
    REJECTED_COACH = 'rejected_coach'
    REJECTED_ATHLETE = 'rejected_athlete'
