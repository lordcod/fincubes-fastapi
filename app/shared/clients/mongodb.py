import motor.motor_asyncio
from app.core.config import settings

COLLECTION_NAME = "best_results"

client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.MONGO_DB_NAME]
