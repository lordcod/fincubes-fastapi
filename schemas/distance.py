from pydantic import BaseModel
from typing import Optional


class DistanceCreateUpdateIn_Pydantic(BaseModel):
    stroke: str
    distance: int
    category: Optional[str] = None
    order: int
    gender: str
    min_year: Optional[int] = None
    max_year: Optional[int] = None


class Distance_Pydantic(DistanceCreateUpdateIn_Pydantic):
    id: int
    competition_id: int

    class Config:
        from_attributes = True


class DistanceOrderUpdate_Pydantic(BaseModel):
    id: int
    order: int

    class Config:
        from_attributes = True
