import asyncio
import os
import sys
from fastapi.testclient import TestClient

sys.path.append(os.getcwd())
test_data_competition = {
    "name": "Соревнование",
    "date": "25 июля 2020",
    "start_date": "2020-06-25",
    "end_date": "2020-06-25",
    "location": "FINCUBES SITE",
    "organizer": "FINCUBES",
    "links": [],
    "status": "ALL",
}


async def test():
    from main import app

    with TestClient(app) as client:
        response = client.get("/")
        print(response.headers, response.request.headers)
        print(
            f"Getting {response.status_code} status, data: {response.read().decode()}"
        )
        assert response.status_code == 404

        response = client.get("/competitions/nearests")
        print(
            f"Getting {response.status_code} status, data: {response.read().decode()}"
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

        response = client.post(
            "/competitions/",
            json=test_data_competition,
            headers={"Authorization": "Bearer " + " "},
        )
        print(
            f"Getting {response.status_code} status, data: {response.read().decode()}"
        )
        assert response.status_code == 403


if __name__ == "__main__":
    asyncio.run(test())
