from tortoise.contrib.pydantic import pydantic_model_creator

from app.models.competition.recent_event import RecentEvent
from app.schemas import with_nested
from app.schemas.competition.competition import Competition_Pydantic

RecentEventIn = pydantic_model_creator(RecentEvent, exclude_readonly=True)
RecentEventOut = RecentEventOut = with_nested(
    pydantic_model_creator(RecentEvent), competition=Competition_Pydantic
)
