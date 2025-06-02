from fastapi.testclient import TestClient
from main import app


def test_read_items():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 404

        response = client.get("/competitions/nearests")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


if __name__ == '__main__':
    test_read_items()
