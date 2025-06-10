import os
from dotenv import load_dotenv

load_dotenv(override=True)

REDIS_URL = os.getenv("REDIS_URL")
DATABASE_URL = os.getenv(
    "DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

TORTOISE_MODELS = ["models.models", "aerich.models"]

TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": TORTOISE_MODELS,
            "default_connection": "default",
        },
    },
}

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

AWS_KEY_ID = os.getenv("AWS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
