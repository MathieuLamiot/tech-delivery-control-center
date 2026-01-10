import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestHealthcheck:
    def test_healthcheck_returns_ok(self):
        client = APIClient()
        response = client.get("/healthcheck/")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
