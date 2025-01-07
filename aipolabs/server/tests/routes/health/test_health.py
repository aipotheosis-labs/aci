import logging

from fastapi.testclient import TestClient

logger = logging.getLogger(__name__)


def test_health_check(test_client: TestClient) -> None:
    # Note: /v1/health will result in a redirect to /v1/health/, in which case the return code is 30X
    response = test_client.get("/v1/health/")
    assert response.status_code == 200
    assert response.json() is True
