from os import getenv
from dotenv import load_dotenv

load_dotenv(override=True)


TORTOISE_ORM = {
    "connections": {"default": getenv('DATABASE_URL')},
    "apps": {
        "models": {
            "models": ["app.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
