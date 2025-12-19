from sqlalchemy import MetaData
from app.models.athlete.athlete import Athlete
from app.models.competition.competition import Competition
from app.models.competition.result import CompetitionResult, CompetitionStage
from app.sql.utils import tortoise_model_to_sqlalchemy_table


metadata = MetaData()
results = tortoise_model_to_sqlalchemy_table(CompetitionResult)
stages = tortoise_model_to_sqlalchemy_table(CompetitionStage)
athletes = tortoise_model_to_sqlalchemy_table(Athlete)
competitions = tortoise_model_to_sqlalchemy_table(Competition)
