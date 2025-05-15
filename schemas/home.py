
from pydantic import BaseModel
from schemas import Athlete_Pydantic
from schemas import Competition_Pydantic


class TopAthleteOut(BaseModel):
    id: int
    athlete: Athlete_Pydantic

    class Config:
        orm_mode = True


class TopAthleteIn(BaseModel):
    athlete_id: int


class RecentEventOut(BaseModel):
    id: int
    competition: Competition_Pydantic

    class Config:
        orm_mode = True


class RecentEventIn(BaseModel):
    competition_id: int
