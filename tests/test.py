import asyncio
from fastapi.testclient import TestClient
from app.main import create_app

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
    with TestClient(create_app('prod')) as client:
        response = client.get("/")
        print(response.headers, response.request.headers)
        print(
            f"Getting {response.status_code} status, data: {response.read().decode()}"
        )
        assert response.status_code == 404


def run():
    asyncio.run(test())


if __name__ == "__main__":
    run()
