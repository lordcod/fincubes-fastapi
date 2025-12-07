import motor.motor_asyncio
from app.core.config import settings

client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URL)
db = client[settings.MONGO_DB_NAME]
