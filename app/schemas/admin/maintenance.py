from typing import Optional

from pydantic import BaseModel


class TransferResultsRequest(BaseModel):
    from_athlete_id: int
    to_athlete_id: int
    competition_id: Optional[int] = None
    apply: bool = False
    delete_empty_source: bool = False


class CompetitionMaintenanceRequest(BaseModel):
    competition_id: int
    apply: bool = False


class ClearEmptyAthletesRequest(BaseModel):
    apply: bool = False


class ChangePasswordRequest(BaseModel):
    user_id: int
    new_password: str
    apply: bool = False
