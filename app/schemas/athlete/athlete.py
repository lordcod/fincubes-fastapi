from pydantic import Field
from tortoise.contrib.pydantic import pydantic_model_creator
from app.schemas import create_pydantic_model, with_nested

from app.models.athlete.athlete import Athlete

AthleteIn_Pydantic = pydantic_model_creator(Athlete, exclude_readonly=True)
Athlete_Pydantic = create_pydantic_model(Athlete)


AthleteDetailed_Pydantic = with_nested(
    create_pydantic_model(Athlete),
    occupied_places_count=(int, Field(0, description="По умолчанию 0")),
    competitions_count=(int, Field(0, description="По умолчанию 0")),
)


AthleteWithStatus_Pydantic = with_nested(
    create_pydantic_model(Athlete),
    status=str
)
