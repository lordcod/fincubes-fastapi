import sys
from typing import List

from pydantic_settings import BaseSettings


class MiddlewareSettings(BaseSettings):
    dev_mode: bool = sys.platform == "win32"

    dev_origins: List[str] = ["*"]
    prod_origins: List[str] = [
        "https://fincubes.ru",
        "https://dev.fincubes.ru",
        "https://next.fincubes.ru",
        "https://fincubes.online",
        "https://fincubes-nextjs.vercel.app",
        "http://localhost:5173",
        "http://localhost:4173",
        "http://localhost:3000",
    ]

    dev_hosts: List[str] = ["*"]
    prod_hosts: List[str] = [
        "testserver",
        "localhost",
        "127.0.0.1",
        "fincubes.ru",
        "*.fincubes.ru",
    ]

    local_server: dict = {
        "url": "http://localhost:8000",
        "description": "Local server"
    }
