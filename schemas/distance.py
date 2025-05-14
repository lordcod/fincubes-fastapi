from pydantic import BaseModel
from typing import Optional


class DistanceCreateUpdateIn_Pydantic(BaseModel):
    stroke: str
    distance: int
    category: Optional[str] = None
    order: int
    gender: str


class Distance_Pydantic(DistanceCreateUpdateIn_Pydantic):
    id: int
    competition_id: int

    class Config:
        orm_mode = True


class DistanceOrderUpdate_Pydantic(BaseModel):
    id: int
    order: int

    class Config:
        orm_mode = True
