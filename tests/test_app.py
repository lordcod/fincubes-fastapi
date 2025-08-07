import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app('prod')
    with TestClient(app) as c:
        yield c


def test_root_returns_404(client):
    response = client.get("/")
    assert response.status_code == 404
