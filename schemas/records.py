from datetime import date
from pydantic import BaseModel
from typing import Optional


class RecordIn(BaseModel):
    stroke: str
    distance: int
    time: str
    firstname: str
    lastname: str
    birth_year: int
    region: str
    date: date
    city: str
    country: Optional[str] = None
    event_name: str
    category: Optional[str] = None
    gender: Optional[str] = None


class RecordOut(RecordIn):
    id: int
