from fastapi.testclient import TestClient
from main import app


def test():
    with TestClient(app) as client:
        response = client.get("/")
        print(
            f'Getting {response.status_code} status, data: {response.json()}')
        assert response.status_code == 404

        response = client.get("/competitions/nearests")
        print(
            f'Getting {response.status_code} status, data: {response.json()}')
        assert response.status_code == 200
        assert isinstance(response.json(), list)


if __name__ == '__main__':
    test()
