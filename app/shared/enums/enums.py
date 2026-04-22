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


class CoachAthleteStatusEnum(StrEnum):
    ACCEPTED = 'accepted'
    PENDING = 'pending'
    REJECTED_COACH = 'rejected_coach'
    REJECTED_ATHLETE = 'rejected_athlete'


class ReviewSessionStatusEnum(StrEnum):
    NEW = "new"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewSourceTypeEnum(StrEnum):
    COMPETITION_RESULTS = "competition_results"


class ReviewItemStatusEnum(StrEnum):
    NEW = "new"
    AUTO_MATCH_CANDIDATE = "auto_match_candidate"
    NEEDS_MANUAL_REVIEW = "needs_manual_review"
    MATCHED_EXISTING = "matched_existing"
    ENRICH_PENDING = "enrich_pending"
    CREATED_NEW = "created_new"
    SKIPPED = "skipped"
    FAILED = "failed"
    DONE = "done"


class ReviewDecisionActionEnum(StrEnum):
    MATCH_EXISTING = "match_existing"
    ENRICH_EXISTING = "enrich_existing"
    CREATE_NEW = "create_new"
    SKIP = "skip"
    MANUAL = "manual"


class ReviewConfidenceEnum(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
