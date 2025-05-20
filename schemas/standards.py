from pydantic import BaseModel
from typing import Optional
from .flexible_time import FlexibleTime


class StandardIn(BaseModel):
    code: str
    stroke: str
    distance: int
    gender: str
    type: str
    result: Optional[FlexibleTime]
    is_active: Optional[bool] = True


class StandardOut(StandardIn):
    id: int

    class Config:
        from_attributes = True
