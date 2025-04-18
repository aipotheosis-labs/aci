import logging

from fastapi import status
from fastapi.testclient import TestClient

from aci.server import config

logger = logging.getLogger(__name__)


def test_health_check(test_client: TestClient) -> None:
    # Note: /v1/health will result in a redirect to /v1/health/, in which case
    # the return code is 30X
    response = test_client.get(f"{config.ROUTER_PREFIX_HEALTH}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is True
