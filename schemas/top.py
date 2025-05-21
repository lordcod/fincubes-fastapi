from typing import List
from pydantic import BaseModel
from schemas.result import Result_Pydantic


class Top_Pydantic(BaseModel):
    stroke: str
    distance: int
    results: List[Result_Pydantic]


class RandomTop_Pydantic(BaseModel):
    stroke: str
    distance: int
