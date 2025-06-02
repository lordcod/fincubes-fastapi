from fastapi.testclient import TestClient
from main import app


def test():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 404, ('Receive %s status' %
                                             response.status_code)

        response = client.get("/competitions/nearests")
        assert response.status_code == 200, ('Receive %s status' %
                                             response.status_code)
        assert isinstance(response.json(), list), 'Receive %s type' % type(
            response.json())


if __name__ == '__main__':
    test()
