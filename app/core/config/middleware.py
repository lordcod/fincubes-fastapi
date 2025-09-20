from typing import List, Optional

from pydantic_settings import BaseSettings


class MiddlewareSettings(BaseSettings):
    dev_origins: List[str] = []
    prod_origins: List[str] = []
    prod_origin_regex: str = r"^(https?:\/\/(.+\.)?(fincubes\.ru|vercel\.app|localhost(:\d{1,5})?))$"

    dev_hosts: List[str] = ["*"]
    prod_hosts: List[str] = [
        "testserver",
        "localhost",
        "127.0.0.1",
        "fincubes.ru",
        "*.fincubes.ru",
        "vercel.com",
        "*.vercel.com",
        "vercel.app",
        "*.vercel.app",
    ]

    local_server: dict = {
        "url": "http://localhost:8000",
        "description": "Local server"
    }
