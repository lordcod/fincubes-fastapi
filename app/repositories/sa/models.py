from sqlalchemy import MetaData
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.relay_leg import RelayLeg
from app.models.competition.relay_result import RelayResult
from app.models.competition.result import Result
from app.sql.utils import tortoise_model_to_sqlalchemy_table


metadata = MetaData()
results = tortoise_model_to_sqlalchemy_table(Result)
athletes = tortoise_model_to_sqlalchemy_table(Athlete)
competitions = tortoise_model_to_sqlalchemy_table(Competition)
relay_results = tortoise_model_to_sqlalchemy_table(RelayResult)
relay_legs = tortoise_model_to_sqlalchemy_table(RelayLeg)
