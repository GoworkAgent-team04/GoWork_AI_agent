import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    response = client.post("/auth/token", json={"user_id": "test-user-1"})
    return response.json()["access_token"]
