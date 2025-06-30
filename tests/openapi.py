import asyncio
import json
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.append(os.getcwd())
CACHE_DIR = Path('./.cache')
CACHE_DIR.mkdir(exist_ok=True)


async def test():
    from app.main import app

    with TestClient(app) as client:
        response = client.get("/openapi.json")
        if response.status_code == 200:
            openapi_data = response.json()
            with open(CACHE_DIR / "openapi.json", "w") as f:
                json.dump(openapi_data, f, indent=4)
        print("OpenAPI спецификация сохранена в файл openapi.json.")

if __name__ == "__main__":
    asyncio.run(test())
